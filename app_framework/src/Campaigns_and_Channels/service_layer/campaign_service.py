# application_name/service_layer/campaign_service.py
from __future__ import annotations
from datetime import date
from typing import Optional, Dict, List

from ..data_layer.db import DB
from ..data_layer.campaign_dao import CampaignDAO
from ..data_layer.channel_dao import ChannelDAO
from ..data_layer.campaign_channel_xref_dao import CampaignChannelXrefDAO


class CampaignService:
    """
    Business logic for campaigns:
      - validate inputs (dates, budget)
      - orchestrate multi-table operations (link/unlink)
      - convenience fetches (campaign with channels, etc.)
    """

    def __init__(self):
        self.campaigns = CampaignDAO()
        self.channels = ChannelDAO()
        self.xref = CampaignChannelXrefDAO()

    # -------------------------
    # Create / Read / Update / Delete
    # -------------------------
    def create_campaign(
        self,
        name: str,
        start_date: Optional[str | date] = None,
        end_date: Optional[str | date] = None,
        budget_cents: int = 0,
        description: Optional[str] = None,
    ) -> int:
        self._validate_campaign_inputs(name, start_date, end_date, budget_cents)
        return self.campaigns.create(
            name=name,
            start_date=start_date,
            end_date=end_date,
            budget_cents=budget_cents,
            description=description,
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
            ids = [c["campaign_id"] for c in items]
            chan_map = self._channels_for_campaigns(ids)
            for c in items:
                c["channels"] = chan_map.get(c["campaign_id"], [])
        return items

    def update_campaign(self, campaign_id: int, **fields) -> int:
        # Validate the fields if present
        if "name" in fields and not fields["name"]:
            raise ValueError("name cannot be empty.")
        if "budget_cents" in fields:
            b = fields["budget_cents"]
            if b is None or int(b) < 0:
                raise ValueError("budget_cents must be >= 0.")
        if "start_date" in fields or "end_date" in fields:
            start = fields.get("start_date", None)
            end = fields.get("end_date", None)
            if start and end and str(end) < str(start):
                raise ValueError("end_date cannot be before start_date.")

        return self.campaigns.update(campaign_id, **fields)

    def delete_campaign(self, campaign_id: int) -> int:
        # With FK ON DELETE CASCADE, links will be removed automatically.
        # If not using cascade, you could call self.xref.purge_campaign first.
        return self.campaigns.delete(campaign_id)

    # -------------------------
    # Linking operations
    # -------------------------
    def attach_channel(self, campaign_id: int, channel_id: int) -> bool:
        """Link channel to campaign. Returns True if newly linked, False if it already existed."""
        self._ensure_exists(campaign_id=campaign_id, channel_id=channel_id)
        # Transaction is overkill with INSERT IGNORE, but this keeps it consistent with future changes.
        with DB.conn() as cn:
            cn.start_transaction()
            try:
                created = self.xref.link(campaign_id, channel_id)
                cn.commit()
                return created
            except Exception:
                cn.rollback()
                raise

    def detach_channel(self, campaign_id: int, channel_id: int) -> int:
        """Unlink channel from campaign. Returns number of rows deleted (0 or 1)."""
        self._ensure_exists(campaign_id=campaign_id, channel_id=channel_id, check_relation=False)
        with DB.conn() as cn:
            cn.start_transaction()
            try:
                deleted = self.xref.unlink(campaign_id, channel_id)
                cn.commit()
                return deleted
            except Exception:
                cn.rollback()
                raise

    # -------------------------
    # Convenience queries
    # -------------------------
    def get_campaign_with_channels(self, campaign_id: int) -> Optional[Dict]:
        c = self.campaigns.get(campaign_id)
        if not c:
            return None
        c["channels"] = self.xref.list_channels_for_campaign(campaign_id)
        return c

    def channels_for_campaign(self, campaign_id: int) -> List[Dict]:
        self._ensure_campaign(campaign_id)
        return self.xref.list_channels_for_campaign(campaign_id)

    def campaigns_for_channel(self, channel_id: int) -> List[Dict]:
        self._ensure_channel(channel_id)
        return self.xref.list_campaigns_for_channel(channel_id)

    # -------------------------
    # Internal helpers
    # -------------------------
    def _validate_campaign_inputs(
        self,
        name: str,
        start_date: Optional[str | date],
        end_date: Optional[str | date],
        budget_cents: int,
    ):
        if not name or not name.strip():
            raise ValueError("name is required.")
        if budget_cents is None or int(budget_cents) < 0:
            raise ValueError("budget_cents must be >= 0.")
        if start_date and end_date and str(end_date) < str(start_date):
            raise ValueError("end_date cannot be before start_date.")

    def _ensure_exists(self, campaign_id: Optional[int] = None, channel_id: Optional[int] = None, check_relation: bool = True):
        if campaign_id is not None:
            self._ensure_campaign(campaign_id)
        if channel_id is not None:
            self._ensure_channel(channel_id)

    def _ensure_campaign(self, campaign_id: int):
        if not self.campaigns.get(campaign_id):
            raise ValueError(f"campaign_id {campaign_id} not found.")

    def _ensure_channel(self, channel_id: int):
        if not self.channels.get(channel_id):
            raise ValueError(f"channel_id {channel_id} not found.")

    def _channels_for_campaigns(self, campaign_ids: List[int]) -> Dict[int, List[Dict]]:
        """
        Batch helper: returns {campaign_id: [channel_rows...]}
        Efficient for list views that show attached channels.
        """
        # Simple approach: loop (OK for small class projects). For large sets, write a single JOIN query.
        out: Dict[int, List[Dict]] = {cid: [] for cid in campaign_ids}
        for cid in campaign_ids:
            out[cid] = self.xref.list_channels_for_campaign(cid)
        return out
