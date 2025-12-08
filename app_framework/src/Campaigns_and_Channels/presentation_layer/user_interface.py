import sys, shlex
from ..data_layer.db import DB
from ..service_layer.campaign_service import CampaignService
from ..data_layer.channel_dao import ChannelDAO
from ..data_layer.campaign_dao import CampaignDAO

class UserInterface:
    def __init__(self, config):
        self.config = config
        DB.init_pool(config)
        self.svc = CampaignService()
        self.campaigns = CampaignDAO()
        self.channels = ChannelDAO()

#----------------------------------------------------------#
#--------------------START SCREEN--------------------------#
#----------------------------------------------------------#
    def start(self):
        print("Advertisment Campaigns CLI. Type 'help' for commands, 'quit' to exit.")
        while True:
            try:
                line = input("> ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\nbye"); return
            if not line: 
                continue
            if line in ("quit", "exit"):
                return
            self.handle(line)

#----------------------------------------------------------#
#-----------------------COMMANDS---------------------------#
#----------------------------------------------------------#
    def handle(self, line):
        try:
            args = shlex.split(line)
            cmd = args[0]

            if cmd == "help":
                self.help()
                return

            if cmd == "campaign:list":
                # pretty formatted campaign list
                self.campaign_list()
                return

            if cmd == "campaign:add":
                # example: campaign:add "Holiday 2025" 2025-11-15 2025-12-31 5000000
                name = args[1]
                sd = args[2] if len(args) > 2 else None
                ed = args[3] if len(args) > 3 else None
                budget = int(args[4]) if len(args) > 4 else 0
                cid = self.svc.create_campaign(name, sd, ed, budget)
                print(f"created campaign_id={cid}")
                return

            if cmd == "campaign:delete":
                # campaign:delete <campaign_id>
                if len(args) < 2:
                    print("Usage: campaign:delete <campaign_id>")
                    return
                cid = int(args[1])
                deleted = self.campaigns.delete(cid)
                if deleted:
                    print(f"deleted campaign_id={cid}")
                else:
                    print(f"no campaign found with id={cid}")
                return

            # NEW: get a single campaign by id
            if cmd == "campaign:get":
                if len(args) < 2:
                    print("Usage: campaign:get <campaign_id>")
                    return
                cid = int(args[1])
                self.campaign_get(cid)
                return

            # NEW: update a campaign
            # Usage: campaign:update <id> <name> [start_date] [end_date] [budget_cents]
            if cmd == "campaign:update":
                if len(args) < 3:
                    print(
                        "Usage: campaign:update <campaign_id> <name> "
                        "[start_date] [end_date] [budget_cents]"
                    )
                    return
                cid = int(args[1])
                name = args[2]
                sd = args[3] if len(args) > 3 else None
                ed = args[4] if len(args) > 4 else None
                budget = int(args[5]) if len(args) > 5 else None
                self.campaign_update(cid, name, sd, ed, budget)
                return

            # NEW: set status of campaign
            # Usage: campaign:set-status <campaign_id> <status>
            if cmd == "campaign:set-status":
                if len(args) < 3:
                    print("Usage: campaign:set-status <campaign_id> <status>")
                    return
                cid = int(args[1])
                status = args[2]
                self.campaign_set_status(cid, status)
                return
            if cmd == "channel:list":
                # pretty formatted channel list
                self.channel_list()
                return

            if cmd == "channel:add":
                # Usage: channel:add <name> [type]
                if len(args) < 2:
                    print("Usage: channel:add <name> [type]")
                    return

                name = args[1]
                ch_type = args[2] if len(args) > 2 else "Other"
                ch = self.channels
                ch_id = ch.create(name, ch_type)
                print(f"created channel_id={ch_id}")
                return

            if cmd == "channel:delete":
                # channel:delete <channel_id> [--force]
                if len(args) < 2:
                    print("Usage: channel:delete <channel_id> [--force]")
                    return
                chid = int(args[1])
                force = ("--force" in args[2:])
                self.channel_delete(chid, force=force)
                return
            
            if cmd == "channel:update":
                if len(args) < 4:
                    print("Usage: channel:update <channel_id> <name> <type>")
                    return
                chid = int(args[1])
                name = args[2]
                ch_type = args[3]
                self.channel_update(chid, name, ch_type)
                return

            if cmd == "link":
                # link <campaign_id> <channel_id>
                cid = int(args[1])
                chid = int(args[2])
                added = self.svc.attach_channel(cid, chid)
                print("linked" if added else "already linked")
                return

            if cmd == "unlink":
                # unlink <campaign_id> <channel_id>
                if len(args) < 3:
                    print("Usage: unlink <campaign_id> <channel_id>")
                    return
                cid = int(args[1])
                chid = int(args[2])
                self.unlink(cid, chid)
                return

            if cmd == "inspect:db":
                self.inspect_db()
                return
        
            print("Unknown command. Try 'help'.")
        except Exception as e:
            print(f"Error: {e}")

#----------------------------------------------------------#
#----------------------HELP FUNC---------------------------#
#----------------------------------------------------------#
    def help(self):
        print("""Commands:
        campaign:list                                         - list campaigns      
        campaign:add <name> [start] [end] [budget_cents]      - create a campaign   
        campaign:delete <campaign_id>                         - delete a campaign
        campaign:get <campaign_id>                            - show a campaign by id
        campaign:update <id> <name> [start] [end] [budget]    - update a campaign
        campaign:set-status <id> <status>                     - set status of a campaign
              
        channel:list                                          - list channels (formatted)
        channel:add <name>                                    - create a channel
        channel:delete <channel_id> [--force]                 - delete a channel
        channel:update <id> <name> <type>                     - update a channel
              
        link <campaign_id> <channel_id>                       - link campaign to channel
        unlink <campaign_id> <channel_id>                     - unlink campaign to channel
  
        inspect:db                                            - pretty-print DB tables snapshot
              
        quit                                                  - exit
""")


#----------------------------------------------------------#
#-----------------------GET LIST---------------------------#
#----------------------------------------------------------#
    def campaign_list(self):
        """Pretty-print channels with aligned columns and | separators."""
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


#----------------------------------------------------------#
#------------------------DELETE----------------------------#
#----------------------------------------------------------#
    def campaign_delete(self, campaign_id: int):
        
        conn = DB.get_connection()
        try:
            cur = conn.cursor()
            # Check if channel is used in mappings
            cur.execute(
                "SELECT COUNT(*) FROM campaign_channel_xref WHERE campaign_id = %s",
                (campaign_id,),
            )
            (count,) = cur.fetchone()

            if count > 0:
                print(
                    f"Campaign {campaign_id} is linked to {count} channel(s). "
                    "Use 'campaign:delete <id>' to delete and remove mappings."
                )
                return

        finally:
            cur.close()
            conn.close()

        # If we got here, it's safe or forced
        deleted = self.campaign.delete(campaign_id)
        if deleted:
            print(f"deleted campaign_id={campaign_id}")
        else:
            print(f"no campaign found with id={campaign_id}")

    def campaign_get(self, campaign_id: int):
        """Fetch and pretty-print a single campaign by id."""
        campaign = self.campaigns.get(campaign_id)
        if not campaign:
            print(f"no campaign found with id={campaign_id}")
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

    def campaign_update(self, campaign_id: int, name: str,
                        start_date: str | None,
                        end_date: str | None,
                        budget_cents: int | None):
        """
        Update fields on a campaign.
        Only non-None fields will be updated.
        """
        fields = {}
        if name:
            fields["name"] = name
        if start_date is not None:
            fields["start_date"] = start_date
        if end_date is not None:
            fields["end_date"] = end_date
        if budget_cents is not None:
            fields["budget_cents"] = budget_cents

        if not fields:
            print("No fields to update.")
            return

        updated = self.campaigns.update(campaign_id, **fields)
        if not updated:
            print(f"no campaign found with id={campaign_id}")
        else:
            print(f"updated campaign_id={campaign_id}")

    def campaign_set_status(self, campaign_id: int, status: str):
        """
        Set the status of a campaign using the existing DAO logic.
        Example statuses might be: 'planned', 'active', 'completed'.
        """
        ok = self.campaigns.set_status(campaign_id, status)
        if not ok:
            print(f"no campaign found with id={campaign_id}")
        else:
            print(f"status for campaign_id={campaign_id} set to '{status}'")

#----------------------------------------------------------#
#------------------------CHANNEL---------------------------#
#----------------------------------------------------------#
#----------------------------------------------------------#
#------------------------GET LIST--------------------------#
#----------------------------------------------------------#
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

#----------------------------------------------------------#
#------------------------DELETE----------------------------#
#----------------------------------------------------------#
    def channel_delete(self, channel_id: int, force: bool = False):
        """
        Safe delete:
        - If the channel is linked to any campaign and not forced, warn and abort.
        - If --force is used, delete the channel (FK CASCADE removes mappings).
        """
        conn = DB.get_connection()
        try:
            cur = conn.cursor()
            # Check if channel is used in mappings
            cur.execute(
                "SELECT COUNT(*) FROM campaign_channel_xref WHERE channel_id = %s",
                (channel_id,),
            )
            (count,) = cur.fetchone()

            if count > 0 and not force:
                print(
                    f"Channel {channel_id} is linked to {count} campaign(s). "
                    "Use 'channel:delete <id> --force' to delete and remove mappings."
                )
                return

        finally:
            cur.close()
            conn.close()

        # If we got here, it's safe or forced
        deleted = self.channels.delete(channel_id)
        if deleted:
            print(f"deleted channel_id={channel_id}")
        else:
            print(f"no channel found with id={channel_id}")


#----------------------------------------------------------#
#------------------------UPDATE----------------------------#
#----------------------------------------------------------#
    def channel_update(self, channel_id: int, name: str, ch_type: str):
        """
        Update a channel's name and/or type.
        """
        fields = {}
        if name:
            fields["name"] = name
        if ch_type:
            fields["type"] = ch_type

        if not fields:
            print("No fields to update.")
            return

        updated = self.channels.update(channel_id, **fields)
        if not updated:
            print(f"no channel found with id={channel_id}")
        else:
            print(f"updated channel_id={channel_id}")

#----------------------------------------------------------#
#------------------------UNLINK----------------------------#
#----------------------------------------------------------#
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
                print(f"unlinked campaign_id={campaign_id} from channel_id={channel_id}")
            else:
                print("no link found to remove")
        finally:
            cur.close()
            conn.close()

#----------------------------------------------------------#
#----------------------INSPECT DB--------------------------#
#----------------------------------------------------------#
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
