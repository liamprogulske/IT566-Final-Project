from __future__ import annotations

from datetime import date
from typing import Optional, Dict, List, Tuple

from ..data_layer.campaign_dao import CampaignDAO
from ..data_layer.channel_dao import ChannelDAO
from ..data_layer.campaign_channel_xref_dao import CampaignChannelXrefDAO


class CampaignService:
    """
    Business logic for campaigns and channels.

    Responsibilities:
      - Validate inputs (dates, budget).
      - Delegate CRUD to DAO layer.
      - Orchestrate multi-table operations (link / unlink).
      - Provide "safe delete" semantics.
      - Manage status updates.
      - Expose performance/metrics helpers.
    """

    def __init__(self) -> None:
        self.campaigns = CampaignDAO()
        self.channels = ChannelDAO()
        self.xref = CampaignChannelXrefDAO()

    # ------------------------------------------------------------------ #
    # Validation helpers
    # ------------------------------------------------------------------ #

    def _validate_dates(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> None:
        if end_date and start_date and end_date < start_date:
            raise ValueError("end_date cannot be before start_date")

    def _validate_budget(self, budget_cents: Optional[int]) -> None:
        if budget_cents is not None and budget_cents < 0:
            raise ValueError("budget_cents cannot be negative")

    # ------------------------------------------------------------------ #
    # Campaign CRUD
    # ------------------------------------------------------------------ #

    def create_campaign(
        self,
        name: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        budget_cents: int = 0,
    ) -> int:
        self._validate_dates(start_date, end_date)
        self._validate_budget(budget_cents)
        return self.campaigns.create(
            name=name,
            start_date=start_date,
            end_date=end_date,
            budget_cents=budget_cents,
        )

    def get_campaign(self, campaign_id: int) -> Optional[Dict]:
        return self.campaigns.get(campaign_id)

    def list_campaigns(
        self,
        limit: int = 50,
        offset: int = 0,
        q: Optional[str] = None,
        include_channels: bool = False,
    ) -> List[Dict]:
        items = self.campaigns.list(limit=limit, offset=offset, q=q)
        if include_channels and items:
            channel_map = self._channels_for_campaigns(
                [c["campaign_id"] for c in items]
            )
            for c in items:
                c["channels"] = channel_map.get(c["campaign_id"], [])
        return items

    def update_campaign(
        self,
        campaign_id: int,
        name: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        budget_cents: Optional[int] = None,
    ) -> bool:
        self._validate_dates(start_date, end_date)
        self._validate_budget(budget_cents)

        fields: Dict[str, object] = {}
        if name is not None:
            fields["name"] = name
        if start_date is not None:
            fields["start_date"] = start_date
        if end_date is not None:
            fields["end_date"] = end_date
        if budget_cents is not None:
            fields["budget_cents"] = budget_cents

        if not fields:
            return False  # nothing to update

        rows = self.campaigns.update(campaign_id, **fields)
        return rows > 0

    def delete_campaign_safe(self, campaign_id: int, force: bool = False) -> Tuple[bool, int]:
        """
        Safe delete:
          - If campaign has linked channels and not force, do NOT delete.
          - If force is True, delete the campaign; FK cascade (or cleanup) handles mappings.
        Returns (deleted, linked_count).
        """
        linked_channels = self.xref.list_channels_for_campaign(campaign_id)
        linked_count = len(linked_channels)

        if linked_count > 0 and not force:
            return False, linked_count

        rows = self.campaigns.delete(campaign_id)
        return rows > 0, linked_count


    def delete_channel_safe(self, channel_id: int, force: bool = False) -> tuple[bool, int]:
        """
        Safe delete for channels:
          - If channel is linked to any campaigns and not force, do NOT delete.
          - If force is True, delete the channel (FK CASCADE cleans xrefs).
        Returns (deleted, linked_count).
        """
        linked_count = self.xref.count_campaigns_for_channel(channel_id)
        if linked_count > 0 and not force:
            return False, linked_count

        rows = self.channels.delete(channel_id)
        return rows > 0, linked_count

    # ------------------------------------------------------------------ #
    # Campaign status
    # ------------------------------------------------------------------ #

    def set_campaign_status(self, campaign_id: int, status: str) -> bool:
        """
        Thin wrapper around CampaignDAO.set_status to keep DB details in DAO.
        """
        status = status.strip().lower()

        # Optional: enforce allowed statuses
        # allowed = {"planned", "active", "paused", "completed", "cancelled"}
        # if status not in allowed:
        #     raise ValueError(
        #         f"Invalid status '{status}'. Must be one of: {', '.join(sorted(allowed))}"
        #     )

        return self.campaigns.set_status(campaign_id, status)

    # ------------------------------------------------------------------ #
    # Channel CRUD
    # ------------------------------------------------------------------ #

    def create_channel(self, name: str, ch_type: str = "Other") -> int:
        return self.channels.create(name, ch_type)

    def list_channels(self, limit: int = 100, offset: int = 0) -> List[Dict]:
        return self.channels.list(limit=limit, offset=offset)

    def update_channel(
        self,
        channel_id: int,
        name: Optional[str] = None,
        ch_type: Optional[str] = None,
    ) -> bool:
        fields: Dict[str, object] = {}
        if name is not None:
            fields["name"] = name
        if ch_type is not None:
            # adapt if your column is 'platform' instead of 'type'
            fields["type"] = ch_type

        if not fields:
            return False

        rows = self.channels.update(channel_id, **fields)
        return rows > 0

    # ------------------------------------------------------------------ #
    # Linking campaigns and channels
    # ------------------------------------------------------------------ #

    def attach_channel(self, campaign_id: int, channel_id: int) -> bool:
        """
        Link channel to campaign.
        Returns True if newly linked, False if it already existed.
        """
        self._ensure_exists(campaign_id=campaign_id, channel_id=channel_id)
        return self.xref.link(campaign_id, channel_id)

    def detach_channel(self, campaign_id: int, channel_id: int) -> int:
        """
        Unlink channel from campaign.
        Returns number of rows deleted (0 or 1).
        """
        return self.xref.unlink(campaign_id, channel_id)

    # ------------------------------------------------------------------ #
    # Channels for a campaign (wrapper used by campaign:channels)
    # ------------------------------------------------------------------ #

    def list_channels_for_campaign(self, campaign_id: int) -> List[Dict]:
        """
        Return list of channel dicts for a campaign.
        """
        self._ensure_exists(campaign_id=campaign_id)
        return self.xref.list_channels_for_campaign(campaign_id)

    # ------------------------------------------------------------------ #
    # Daily metrics: upsert + aggregate performance
    # ------------------------------------------------------------------ #

    def upsert_campaign_daily_metrics(
        self,
        campaign_id: int,
        metric_date: date,
        impressions: int = 0,
        clicks: int = 0,
        spend_cents: int = 0,
        revenue_cents: int = 0,
    ) -> None:
        """
        Insert or update a daily metrics row for a campaign.
        """
        self._ensure_exists(campaign_id=campaign_id)
        self.xref.upsert_campaign_daily_metrics(
            campaign_id,
            metric_date,
            impressions,
            clicks,
            spend_cents,
            revenue_cents,
        )

    def get_campaign_performance(
        self,
        campaign_id: int,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> Dict:
        """
        Return aggregated performance for a campaign over an optional date range.
        """
        self._ensure_exists(campaign_id=campaign_id)
        return self.xref.get_campaign_performance(
            campaign_id,
            start_date=start_date,
            end_date=end_date,
        )

    # ------------------------------------------------------------------ #
    # Internal helpers
    # ------------------------------------------------------------------ #

    def _ensure_exists(
        self,
        campaign_id: Optional[int] = None,
        channel_id: Optional[int] = None,
    ) -> None:
        if campaign_id is not None:
            if not self.campaigns.get(campaign_id):
                raise ValueError(f"campaign_id {campaign_id} not found.")
        if channel_id is not None:
            if not self.channels.get(channel_id):
                raise ValueError(f"channel_id {channel_id} not found.")

    def _channels_for_campaigns(self, campaign_ids: List[int]) -> Dict[int, List[Dict]]:
        """
        Batch helper: returns {campaign_id: [channel_rows...]}.
        """
        out: Dict[int, List[Dict]] = {cid: [] for cid in campaign_ids}
        for cid in campaign_ids:
            out[cid] = self.xref.list_channels_for_campaign(cid)
        return out

    def inspect_database(self) -> dict:
        """
        Return a structured snapshot of the main tables for reporting:
          - campaigns
          - channels
          - mappings (campaign ↔ channel)
        UI is responsible for pretty-printing only.
        """
        campaigns = self.campaigns.list(limit=1000, offset=0)
        channels = self.channels.list(limit=1000, offset=0)
        mappings = self.xref.list_all_mappings()
        return {
            "campaigns": campaigns,
            "channels": channels,
            "mappings": mappings,
        }
