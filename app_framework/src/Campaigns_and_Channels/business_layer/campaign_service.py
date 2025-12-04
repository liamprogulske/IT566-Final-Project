from datetime import date
from ..data_layer.campaign_dao import CampaignDAO
from ..data_layer.channel_dao import ChannelDAO
from ..data_layer.campaign_channel_xref_dao import CampaignChannelXrefDAO
from ..data_layer.db import DB

class CampaignService:
    def __init__(self):
        self.campaigns = CampaignDAO()
        self.channels = ChannelDAO()
        self.xref = CampaignChannelXrefDAO()

    def create_campaign(self, name, start_date=None, end_date=None, budget_cents=0):
        if end_date and start_date and end_date < start_date:
            raise ValueError("end_date cannot be before start_date")
        return self.campaigns.create(name, start_date, end_date, budget_cents)

    def attach_channel(self, campaign_id, channel_id):
        # ensure both exist
        if not self.campaigns.get(campaign_id):
            raise ValueError("campaign not found")
        if not self.channels.get(channel_id):
            raise ValueError("channel not found")

        # transaction to enforce uniqueness
        with DB.conn() as cn:
            cn.start_transaction()
            try:
                with cn.cursor() as cur:
                    cur.execute("""SELECT 1 FROM campaign_channel_xref
                                   WHERE campaign_id=%s AND channel_id=%s""",
                                (campaign_id, channel_id))
                    if cur.fetchone():  # already linked
                        cn.rollback(); return 0
                    cur.execute("""INSERT INTO campaign_channel_xref(campaign_id, channel_id)
                                   VALUES(%s,%s)""", (campaign_id, channel_id))
                cn.commit(); return 1
            except:
                cn.rollback(); raise


