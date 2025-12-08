import sys
import shlex
from datetime import date

from ..data_layer.db import DB
from ..service_layer.campaign_service import CampaignService
from ..data_layer.channel_dao import ChannelDAO
from ..data_layer.campaign_dao import CampaignDAO
from ..data_layer.campaign_channel_xref_dao import CampaignChannelXrefDAO
from datetime import date as _date
# Optional: simple pretty printer for messages (E2)
class UIPrinter:
    RESET = "\033[0m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    CYAN = "\033[96m"
    YELLOW = "\033[93m"

    @classmethod
    def _box(cls, title: str, lines: list[str], color: str) -> None:
        content_lines = [title] + lines
        width = max(len(line) for line in content_lines)
        border = "+" + "-" * (width + 2) + "+"

        print(color + border)
        for i, line in enumerate(content_lines):
            print(f"| {line.ljust(width)} |")
            if i == 0 and len(content_lines) > 1:
                print("|" + "-" * (width + 2) + "|")
        print(border + cls.RESET)

    @classmethod
    def info(cls, title: str, *lines: str) -> None:
        cls._box(title, list(lines), cls.CYAN)

    @classmethod
    def success(cls, title: str, *lines: str) -> None:
        cls._box(title, list(lines), cls.GREEN)

    @classmethod
    def error(cls, title: str, *lines: str) -> None:
        cls._box(title, list(lines), cls.RED)

    @classmethod
    def warn(cls, title: str, *lines: str) -> None:
        cls._box(title, list(lines), cls.YELLOW)


class UserInterface:
    def __init__(self, config):
        self.config = config
        DB.init_pool(config)

        self.svc = CampaignService()
        self.campaigns = CampaignDAO()
        self.channels = ChannelDAO()
        # -------------------------------------------------------------- #
        # Command dispatch table: cmd -> handler(args)
        # -------------------------------------------------------------- #
        self.commands = {
            "help": self.cmd_help,
            
            "campaign:list": self.cmd_campaign_list,
            "campaign:add": self.cmd_campaign_add,
            "campaign:delete": self.cmd_campaign_delete,
            "campaign:get": self.cmd_campaign_get,
            "campaign:update": self.cmd_campaign_update,
            "campaign:set-status": self.cmd_campaign_set_status,
            
            "campaign:channels": self.cmd_campaign_channels,
            "campaign:perf": self.cmd_campaign_perf,
            "campaign:metrics:upsert": self.cmd_campaign_metrics_upsert,


            "channel:list": self.cmd_channel_list,
            "channel:add": self.cmd_channel_add,
            "channel:delete": self.cmd_channel_delete,
            "channel:update": self.cmd_channel_update,
            "link": self.cmd_link,
            "unlink": self.cmd_unlink,
            "inspect:db": self.cmd_inspect_db,
        }

    # ---------------------------------------------------------- #
    # Small helpers for pretty messages
    # ---------------------------------------------------------- #
    def print_error(self, msg: str):
        UIPrinter.error("ERROR", msg)

    def print_success(self, msg: str):
        UIPrinter.success("SUCCESS", msg)

    def print_info(self, msg: str):
        UIPrinter.info("INFO", msg)

    # ---------------------------------------------------------- #
    # START SCREEN / LOOP
    # ---------------------------------------------------------- #
    def start(self):
        print("Advertisment Campaigns CLI. Type 'help' for commands, 'quit' to exit.")
        while True:
            try:
                line = input("> ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\nbye")
                return

            if not line:
                continue
            if line in ("quit", "exit"):
                return

            self.handle(line)

    # ---------------------------------------------------------- #
    # COMMAND DISPATCH
    # ---------------------------------------------------------- #
    def handle(self, line: str):
        try:
            args = shlex.split(line)
            if not args:
                return
            cmd = args[0]

            handler = self.commands.get(cmd)
            if not handler:
                self.print_error(f"Unknown command: {cmd}. Try 'help'.")
                return

            handler(args)
        except Exception as e:
            self.print_error(str(e))

    # ---------------------------------------------------------- #
    # HELP
    # ---------------------------------------------------------- #
    def help(self):
        print("""Commands:
        campaign:list                                         - list campaigns      
        campaign:add <name> [start] [end] [budget_cents]      - create a campaign   
        campaign:delete <campaign_id> [--force]               - delete a campaign (safe delete)
        campaign:get <campaign_id>                            - show a campaign by id
        campaign:update <id> <name> [start] [end] [budget]    - update a campaign
        campaign:set-status <id> <status>                     - set status of a campaign
              
        campaign:channels <campaign_id>                       - list channels for a campaign
        campaign:perf <campaign_id> [start] [end]             - show campaign performance over a date range
        campaign:metrics:upsert <id> <date> <impr> <clicks> <spend_cents> [revenue_cents]
                                                              - upsert daily metrics row
              
        channel:list                                          - list channels (formatted)
        channel:add <name> [type]                             - create a channel
        channel:delete <channel_id> [--force]                 - delete a channel
        channel:update <id> <name> <type>                     - update a channel
              
        link <campaign_id> <channel_id>                       - link campaign to channel
        unlink <campaign_id> <channel_id>                     - unlink campaign to channel
  
        inspect:db                                            - pretty-print DB tables snapshot
              
        quit                                                  - exit
""")

    # command wrapper for dispatch
    def cmd_help(self, args):  # noqa: ARG002
        self.help()

    # ---------------------------------------------------------- #
    # CAMPAIGN COMMANDS
    # ---------------------------------------------------------- #
    def cmd_campaign_list(self, args):  # noqa: ARG002
        self.campaign_list()

    def cmd_campaign_add(self, args):
        # campaign:add "Holiday 2025" 2025-11-15 2025-12-31 5000000
        if len(args) < 2:
            self.print_error("Usage: campaign:add <name> [start] [end] [budget_cents]")
            return

        name = args[1]
        sd = args[2] if len(args) > 2 else None
        ed = args[3] if len(args) > 3 else None
        budget = int(args[4]) if len(args) > 4 else 0

        # dates as strings are acceptable if your DAO expects strings;
        # if you want real date objects, convert here with date.fromisoformat.
        cid = self.svc.create_campaign(name, sd, ed, budget)
        self.print_success(f"created campaign_id={cid}")

    def cmd_campaign_delete(self, args):
        # campaign:delete <campaign_id> [--force]
        if len(args) < 2:
            self.print_error("Usage: campaign:delete <campaign_id> [--force]")
            return
        cid = int(args[1])
        force = ("--force" in args[2:])

        deleted, linked = self.svc.delete_campaign_safe(cid, force=force)
        if not deleted and linked > 0 and not force:
            self.print_error(
                f"Campaign {cid} is linked to {linked} channel(s). "
                "Use 'campaign:delete <id> --force' to delete and remove mappings."
            )
        elif deleted:
            self.print_success(f"deleted campaign_id={cid}")
        else:
            self.print_info(f"no campaign found with id={cid}")

    def cmd_campaign_get(self, args):
        if len(args) < 2:
            self.print_error("Usage: campaign:get <campaign_id>")
            return
        cid = int(args[1])
        self.campaign_get(c_id=cid)

    def cmd_campaign_update(self, args):
        # campaign:update <id> <name> [start_date] [end_date] [budget_cents]
        if len(args) < 3:
            self.print_error(
                "Usage: campaign:update <campaign_id> <name> [start_date] [end_date] [budget_cents]"
            )
            return
        cid = int(args[1])
        name = args[2]
        sd = args[3] if len(args) > 3 else None
        ed = args[4] if len(args) > 4 else None
        budget = int(args[5]) if len(args) > 5 else None

        updated = self.svc.update_campaign(cid, name, sd, ed, budget)
        if not updated:
            self.print_info(f"no campaign found with id={cid} or nothing to update")
        else:
            self.print_success(f"updated campaign_id={cid}")

    def cmd_campaign_set_status(self, args):
        # campaign:set-status <id> <status>
        if len(args) < 3:
            self.print_error("Usage: campaign:set-status <campaign_id> <status>")
            return
        cid = int(args[1])
        status = args[2]

        ok = self.svc.set_campaign_status(cid, status)
        if not ok:
            self.print_info(f"no campaign found with id={cid}")
        else:
            self.print_success(f"status for campaign_id={cid} set to '{status}'")

    def cmd_campaign_channels(self, args):
        # campaign:channels <campaign_id>
        if len(args) < 2:
            self.print_error("Usage: campaign:channels <campaign_id>")
            return

        try:
            cid = int(args[1])
        except ValueError:
            self.print_error("campaign_id must be an integer")
            return

        try:
            channels = self.svc.list_channels_for_campaign(cid)
        except ValueError as e:
            self.print_error(str(e))
            return

        if not channels:
            self.print_info(f"No channels linked to campaign_id={cid}")
            return

        print(f"\n------- CHANNELS FOR CAMPAIGN {cid} -------\n")
        print("+-----+----------------------------+-----------+-----------------------+")
        print("| ID  | NAME                       | TYPE      | CREATED_AT            |")
        print("+-----+----------------------------+-----------+-----------------------+")
        for ch in channels:
            print(
                f"|{ch['channel_id']:>4} | "
                f"{ch['name']:<26.27} | "
                f"{ch['type']:<9} | "
                f"{ch.get('created_at')}   |"
            )
        print("+-----+----------------------------+-----------+-----------------------+")
        print()


    def cmd_campaign_perf(self, args):
        # campaign:perf <campaign_id> [start_date] [end_date]
        if len(args) < 2:
            self.print_error("Usage: campaign:perf <campaign_id> [start_date] [end_date]")
            return

        try:
            cid = int(args[1])
        except ValueError:
            self.print_error("campaign_id must be an integer")
            return

        start = None
        end = None

        if len(args) > 2 and args[2] != "-":
            try:
                start = _date.fromisoformat(args[2])
            except ValueError:
                self.print_error("start_date must be YYYY-MM-DD or '-'")
                return

        if len(args) > 3 and args[3] != "-":
            try:
                end = _date.fromisoformat(args[3])
            except ValueError:
                self.print_error("end_date must be YYYY-MM-DD or '-'")
                return

        try:
            perf = self.svc.get_campaign_performance(cid, start, end)
        except ValueError as e:
            self.print_error(str(e))
            return

        self._print_performance_summary(perf)



    def cmd_campaign_perf(self, args):
        # campaign:perf <campaign_id> [start_date] [end_date]
        if len(args) < 2:
            self.print_error("Usage: campaign:perf <campaign_id> [start_date] [end_date]")
            return

        try:
            cid = int(args[1])
        except ValueError:
            self.print_error("campaign_id must be an integer")
            return

        start = None
        end = None


        if len(args) > 2 and args[2] != "-":
            try:
                start = _date.fromisoformat(args[2])
            except ValueError:
                self.print_error("start_date must be YYYY-MM-DD or '-'")
                return

        if len(args) > 3 and args[3] != "-":
            try:
                end = _date.fromisoformat(args[3])
            except ValueError:
                self.print_error("end_date must be YYYY-MM-DD or '-'")
                return

        try:
            perf = self.svc.get_campaign_performance(cid, start, end)
        except ValueError as e:
            self.print_error(str(e))
            return

        self._print_performance_summary(perf)

    # ---------------------------------------------------------- #
    # CHANNEL COMMANDS
    # ---------------------------------------------------------- #
    def cmd_channel_list(self, args):  # noqa: ARG002
        self.channel_list()

    def cmd_channel_add(self, args):
        # channel:add <name> [type]
        if len(args) < 2:
            self.print_error("Usage: channel:add <name> [type]")
            return
        name = args[1]
        ch_type = args[2] if len(args) > 2 else "Other"

        ch_id = self.svc.create_channel(name, ch_type)
        self.print_success(f"created channel_id={ch_id}")

    def cmd_channel_delete(self, args):
        # channel:delete <channel_id> [--force]
        if len(args) < 2:
            self.print_error("Usage: channel:delete <channel_id> [--force]")
            return
        chid = int(args[1])
        force = ("--force" in args[2:])
        self.channel_delete(chid, force=force)

    def cmd_channel_update(self, args):
        # channel:update <id> <name> <type>
        if len(args) < 4:
            self.print_error("Usage: channel:update <channel_id> <name> <type>")
            return
        chid = int(args[1])
        name = args[2]
        ch_type = args[3]

        updated = self.svc.update_channel(chid, name, ch_type)
        if not updated:
            self.print_info(f"no channel found with id={chid} or nothing to update")
        else:
            self.print_success(f"updated channel_id={chid}")


    def _print_performance_summary(self, perf: dict):
        cid = perf["campaign_id"]
        start = perf.get("start_date")
        end = perf.get("end_date")
        impressions = perf["impressions"]
        clicks = perf["clicks"]
        spend_cents = perf["spend_cents"]
        revenue_cents = perf["revenue_cents"]
        ctr = perf["ctr"]
        cpc = perf["cpc"]
        roas = perf["roas"]

        spend_usd = spend_cents / 100.0
        revenue_usd = revenue_cents / 100.0

        date_range = f"{start} → {end}" if (start or end) else "All Time"

        print(f"\n------- PERFORMANCE FOR CAMPAIGN {cid} -------\n")
        print(f"Date Range   : {date_range}")
        print(f"Impressions  : {impressions}")
        print(f"Clicks       : {clicks}")
        print(f"Spend        : {spend_usd:.2f} USD")
        print(f"Revenue      : {revenue_usd:.2f} USD")
        print()
        print(f"CTR          : {ctr * 100:.2f}%")
        print(f"CPC          : {cpc:.4f} USD/click")
        print(f"ROAS         : {roas:.4f} (revenue / spend)")
        print("\n---------------------------------------------\n")



    def cmd_campaign_metrics_upsert(self, args):
        # campaign:metrics:upsert <id> <date> <impr> <clicks> <spend_cents> [revenue_cents]
        if len(args) < 6:
            self.print_error(
                "Usage: campaign:metrics:upsert <campaign_id> <date> "
                "<impressions> <clicks> <spend_cents> [revenue_cents]"
            )
            return

        

        try:
            cid = int(args[1])
        except ValueError:
            self.print_error("campaign_id must be an integer")
            return

        try:
            metric_date = _date.fromisoformat(args[2])
        except ValueError:
            self.print_error("date must be YYYY-MM-DD")
            return

        try:
            impressions = int(args[3])
            clicks = int(args[4])
            spend_cents = int(args[5])
            revenue_cents = int(args[6]) if len(args) > 6 else 0
        except ValueError:
            self.print_error("impressions, clicks, spend_cents, revenue_cents must be integers")
            return

        try:
            self.svc.upsert_campaign_daily_metrics(
                cid,
                metric_date,
                impressions=impressions,
                clicks=clicks,
                spend_cents=spend_cents,
                revenue_cents=revenue_cents,
            )
        except ValueError as e:
            self.print_error(str(e))
            return

        self.print_success(
            f"Upserted metrics for campaign_id={cid} on {metric_date} "
            f"(impr={impressions}, clicks={clicks}, spend_cents={spend_cents}, revenue_cents={revenue_cents})"
        )



    # ---------------------------------------------------------- #
    # LINK / UNLINK / INSPECT COMMANDS
    # ---------------------------------------------------------- #
    def cmd_link(self, args):
        # link <campaign_id> <channel_id>
        if len(args) < 3:
            self.print_error("Usage: link <campaign_id> <channel_id>")
            return
        cid = int(args[1])
        chid = int(args[2])

        added = self.svc.attach_channel(cid, chid)
        self.print_success("linked" if added else "already linked")

    def cmd_unlink(self, args):
        # unlink <campaign_id> <channel_id>
        if len(args) < 3:
            self.print_error("Usage: unlink <campaign_id> <channel_id>")
            return
        cid = int(args[1])
        chid = int(args[2])
        self.unlink(cid, chid)

    def cmd_inspect_db(self, args):  # noqa: ARG002
        self.inspect_db()

    # ---------------------------------------------------------- #
    # EXISTING METHODS: LIST / GET / DELETE / UNLINK / INSPECT
    # (these are mostly unchanged, just used by the cmd_* wrappers)
    # ---------------------------------------------------------- #
    def campaign_list(self):
        """Pretty-print campaigns with aligned columns and | separators."""
        conn = DB.get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                "SELECT campaign_id, name, status, budget_cents, created_at "
                "FROM campaign ORDER BY campaign_id"
            )
            print("\n--------------- CAMPAIGNS ---------------\n")
            print("+-----+----------------------------+-----------+---------------+--------------+------------------------+")
            print("| ID  | NAME                       | STATUS    | BUDGET_CENTS  | BUDGET_USD   | CREATED_AT             |")
            print("+-----+----------------------------+-----------+---------------+--------------+------------------------+")
            for cid, name, status, budget_cents, created_at in cur:
                budget_usd = (budget_cents or 0) / 100.0
                print(
                    f"|{cid:>4} | "
                    f"{name:<26.27} | "
                    f"{status:<9} | "
                    f"{budget_cents:>13} | "
                    f"{budget_usd:>12.2f} | "
                    f"{created_at}    |"
                )
            print("+-----+----------------------------+-----------+---------------+--------------+------------------------+")
        finally:
            cur.close()
            conn.close()

    def campaign_get(self, c_id: int):
        """Fetch and pretty-print a single campaign by id using DAO."""
        campaign = self.campaigns.get(c_id)
        if not campaign:
            self.print_info(f"no campaign found with id={c_id}")
            return

        print("\n------------ CAMPAIGN DETAIL ------------\n")
        print(f"ID:       {campaign.get('campaign_id')}")
        print(f"Name:     {campaign.get('name')}")
        print(f"Status:   {campaign.get('status')}")
        print(f"Start:    {campaign.get('start_date')}")
        print(f"End:      {campaign.get('end_date')}")
        print(f"Budget:   {campaign.get('budget_cents')} cents")
        print(f"Created:  {campaign.get('created_at')}")
        print("\n----------------------------------------\n")

    def channel_list(self):
        """Pretty-print channels with aligned columns and | separators."""
        conn = DB.get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                "SELECT channel_id, name, type, created_at "
                "FROM channel ORDER BY channel_id"
            )

            print("\n--------------- CHANNELS ---------------\n")
            print("+-----+----------------------------+-----------+-----------------------+")
            print("| ID  | NAME                       | TYPE      | CREATED_AT            |")
            print("+-----+----------------------------+-----------+-----------------------+")

            for channel_id, name, ch_type, created_at in cur:
                print(
                    f"|{channel_id:>4} | "
                    f"{name:<26.27} | "
                    f"{ch_type:<9} | "
                    f"{created_at}   | "
                )
            print("+-----+----------------------------+-----------+-----------------------+")
            print()
        finally:
            cur.close()
            conn.close()

    def channel_delete(self, channel_id: int, force: bool = False):
        """
        Safe delete:
        - If the channel is linked to any campaign and not forced, warn and abort.
        - If --force is used, delete the channel (FK CASCADE removes mappings).
        """
        conn = DB.get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                "SELECT COUNT(*) FROM campaign_channel_xref WHERE channel_id = %s",
                (channel_id,),
            )
            (count,) = cur.fetchone()
        finally:
            cur.close()
            conn.close()

        if count > 0 and not force:
            self.print_error(
                f"Channel {channel_id} is linked to {count} campaign(s). "
                "Use 'channel:delete <id> --force' to delete and remove mappings."
            )
            return

        deleted = self.channels.delete(channel_id)
        if deleted:
            self.print_success(f"deleted channel_id={channel_id}")
        else:
            self.print_info(f"no channel found with id={channel_id}")

    def unlink(self, campaign_id: int, channel_id: int):
        """Remove a single campaign ↔ channel mapping."""
        conn = DB.get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                "DELETE FROM campaign_channel_xref "
                "WHERE campaign_id = %s AND channel_id = %s",
                (campaign_id, channel_id),
            )
            conn.commit()
            if cur.rowcount:
                self.print_success(
                    f"unlinked campaign_id={campaign_id} from channel_id={channel_id}"
                )
            else:
                self.print_info("no link found to remove")
        finally:
            cur.close()
            conn.close()

    def inspect_db(self):
        """Pretty-print the main tables with aligned columns and | separators."""
        conn = DB.get_connection()
        try:
            cur = conn.cursor()

            # CHANNELS
            cur.execute(
                "SELECT channel_id, name, type, created_at "
                "FROM channel ORDER BY channel_id"
            )
            print("\n--------------- CHANNELS ---------------\n")
            print("------+----------------------------+-----------+------------------------")
            print("| ID  | NAME                       | TYPE      | CREATED_AT            |")
            print("------+----------------------------+-----------+------------------------")
            for channel_id, name, ch_type, created_at in cur:
                print(
                    f"|{channel_id:>4} | "
                    f"{name:<26.27} | "
                    f"{ch_type:<9} | "
                    f"{created_at}   | "
                )
            print("------+----------------------------+-----------+------------------------")
            print()

            # CAMPAIGNS
            cur.execute(
                "SELECT campaign_id, name, status, budget_cents, created_at "
                "FROM campaign ORDER BY campaign_id"
            )
            print("\n--------------- CAMPAIGNS ---------------\n")
            print("+-----+----------------------------+-----------+---------------+--------------+------------------------+")
            print("| ID  | NAME                       | STATUS    | BUDGET_CENTS  | BUDGET_USD   | CREATED_AT             |")
            print("+-----+----------------------------+-----------+---------------+--------------+------------------------+")
            for cid, name, status, budget_cents, created_at in cur:
                budget_usd = (budget_cents or 0) / 100.0
                print(
                    f"|{cid:>4} | "
                    f"{name:<26.27} | "
                    f"{status:<9} | "
                    f"{budget_cents:>13} | "
                    f"{budget_usd:>12.2f} | "
                    f"{created_at}    |"
                )
            print("+-----+----------------------------+-----------+---------------+--------------+------------------------+")

            # MAPPINGS
            print("\n--------- CAMPAIGN TO CHANNEL MAPPINGS ---------\n")
            print("+-------------+----------------------------+------------+----------------------------+")
            print("| CAMPAIGN_ID | CAMPAIGN                   | CHANNEL_ID | CHANNEL                    |")
            print("+-------------+----------------------------+------------+----------------------------+")
            cur.execute(
                "SELECT ccx.campaign_id, c.name, ccx.channel_id, ch.name "
                "FROM campaign_channel_xref ccx "
                "JOIN campaign c ON ccx.campaign_id = c.campaign_id "
                "JOIN channel ch ON ccx.channel_id = ch.channel_id "
                "ORDER BY ccx.campaign_id, ccx.channel_id"
            )
            for cmp_id, campaign_name, ch_id, channel_name in cur:
                print(
                    f"|{cmp_id:>11}  | "
                    f"{campaign_name:<26.27} | "
                    f"{ch_id:<10} | "
                    f"{channel_name:<26.27} |"
                )
            print("+-------------+----------------------------+------------+----------------------------+")
            print("\n---------------- END OF REPORT ----------------\n")
        finally:
            cur.close()
            conn.close()
