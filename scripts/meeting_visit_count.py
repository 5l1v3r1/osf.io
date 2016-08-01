#!/usr/bin/env python
# encoding: utf-8

import logging
import requests
from modularodm import Q

from framework.celery_tasks import app as celery_app

from website import settings
from website.app import init_app
from framework.transactions.context import TokuTransaction
from website.models import Tag, Conference, Node
from website.files.models import StoredFileNode
from scripts import utils as scripts_utils

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def main(dry_run=True):
    init_app(routes=False)
    for conf in Conference.find():
        count = 0
        for tag in Tag.find(Q('lower', 'eq', conf.endpoint.lower())):
            for node in Node.find(Q('is_public', 'eq', True) & Q('is_deleted', 'eq', False) & Q('tags', 'eq', tag)):
                record = next(
                    x for x in
                    StoredFileNode.find(
                        Q('node', 'eq', node) &
                        Q('is_file', 'eq', True)
                    ).limit(1)
                ).wrapped()

                if not dry_run:
                    url = 'https://api.keen.io/3.0/projects/{}/events/meeting_view' \
                          '?api_key={}&event_collection=pageviews&timezone=UTC&timeframe=this_14_days' \
                          '&filters=%5B%7B%22property_name%22%3A%22page.info.path%22%2C%22' \
                          'operator%22%3A%22eq%22%2C%22property_value%22%3A%22{}%22%7D%5D'.format(
                            settings.KEEN['public']['project_id'],
                            settings.KEEN['public']['read_key'],
                            record._id)

                    resp = requests.get(url)
                    record.visit = resp.json()['result']
                    record.save()
                    count += 1

        logger.info('Get visit counts for {} projects in Conference {}'.format(count, conf.name))
    

@celery_app.task(name='scripts.meeting_visit_count')
def run_main(dry_run=True):
    scripts_utils.add_file_logger(logger, __file__)
    with TokuTransaction():
        main(dry_run=dry_run)
