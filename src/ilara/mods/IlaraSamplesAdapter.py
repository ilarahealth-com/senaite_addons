from bika.lims import api
from senaite.core.listing.interfaces import IListingView
from senaite.core.listing.interfaces import IListingViewAdapter
from zope.component import adapts
from zope.interface import implements
from bika.lims import logger


class IlaraSamplesAdapter(object):
    adapts(IListingView)
    implements(IListingViewAdapter)
    # Order of priority of this subscriber adapter over others
    priority_order = 1000

    def __init__(self, listing, context):
        self.listing = listing
        self.context = context

    def before_render(self):
        # Add a new filter status
        # draft_status = {
        #     "id": "draft",
        #     "title": "Draft",
        #     "contentFilter": {
        #         "review_state": "sample_draft",
        #         "sort_on": "created",
        #         "sort_order": "descending",
        #     },
        #     "columns": self.listing.columns.keys(),
        # }
        # self.listing.review_states.append(draft_status)

        # Add the column
        self.listing.columns["request_payment"] = {
            "title": "Request Payment",
            "sortable": False,
            "toggle": True,
        }

        # Make the new column visible for only published results
        for filter in self.listing.review_states:
            filter.update({"columns": self.listing.columns.keys()})
            # if filter.get("id") == "published":

    def folder_item(self, obj, item, index):
        # base_url = 'http://localhost:8081/'
        base_url = "http://35.190.90.81/"

        sample = api.get_object(obj)
        sample_title = sample.Title()
        doctor_url = sample.getContactURL()
        host = doctor_url.split("/")[1]
        logger.info("Host: {0}".format(host))

        payment_app_url = base_url + "payments?sampleid={0}&host={1}".format(
            sample_title, host
        )
        item["request_payment"] = (
            "<a href='%s' target='_blank'>Not paid</a>" % payment_app_url
        )

        payment_results = api.search({"portal_type": "payment", "title": sample_title})
        payments = map(api.get_object, payment_results)
        # logger.info('Payments found: {0}'.format(len(payments)))

        if len(payments) > 0:
            sorted_payments = sorted(
                payments, key=lambda payment: payment.date_requested, reverse=True
            )
            latest_payment = sorted_payments[0]

            logger.info(
                "A payment request was made for {0}".format(latest_payment.title)
            )
            logger.info("ID: {0}".format(latest_payment.id))
            logger.info("Is consolidated: {0}".format(latest_payment.is_consolidated))
            logger.info("Result code: {0}".format(latest_payment.mpesa_resultcode))
            logger.info("Response code: {0}".format(latest_payment.mpesa_responsecode))

            if latest_payment.is_consolidated == "True":
                logger.info(sample_title + ": is a consolidated payment")
                item["request_payment"] = (
                    "<a href='%s' target='_blank'>Consolidated Payment</a>"
                    % payment_app_url
                )

            if latest_payment.is_consolidated == "False":
                logger.info(sample_title + ": not a consolidated payment")
                if (
                    latest_payment.mpesa_resultcode == None
                    and latest_payment.mpesa_responsecode == "0"
                ):
                    logger.info(sample_title + ": Incomplete")
                    item["request_payment"] = (
                        "<a href='%s' target='_blank'>Incomplete Payment</a>"
                        % payment_app_url
                    )
                if latest_payment.mpesa_resultcode == "0":
                    logger.info(sample_title + ": Paid")
                    item["request_payment"] = (
                        "<a href='%s' target='_blank'>Paid</a>" % payment_app_url
                    )

        return item
