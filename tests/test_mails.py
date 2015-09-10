# -*- coding: utf-8 -*-
import mock
from datetime import datetime, timedelta
from nose.tools import *  # PEP 8 sserts

from website import mails, settings
from tests import factories
from tests.base import OsfTestCase

def test_plain_mail():
    mail = mails.Mail('test', subject='A test email to ${name}')
    rendered = mail.text(name='World')
    assert_equal(rendered.strip(), 'Hello World')
    assert_equal(mail.subject(name='World'), 'A test email to World')


def test_html_mail():
    mail = mails.Mail('test', subject='A test email')
    rendered = mail.html(name='World')
    assert_equal(rendered.strip(), 'Hello <p>World</p>')

class TestQueuedMail(OsfTestCase):
    def setUp(self):
        OsfTestCase.setUp(self)
        self.user = factories.AuthUserFactory()
        self.user.is_registered = True
        self.user.save()

    def test_no_login_callback_for_active_user(self):
        mail = mails.QueuedMail()
        mail.create(
            to_addr=self.user.username,
            send_at=datetime.utcnow(),
            user=self.user,
            mail=mails.NO_LOGIN,
            fullname=self.user.fullname
        )
        self.user.date_last_login = datetime.utcnow() + timedelta(seconds=10)
        self.user.save()
        assert_false(mail.send_mail())

    def test_no_login_callback_for_inactive_user(self):
        self.user.date_last_login = datetime.utcnow() - timedelta(weeks=10)
        self.user.save()
        mail = mails.QueuedMail()
        mail.create(
            to_addr=self.user.username,
            send_at=datetime.utcnow(),
            user=self.user,
            mail=mails.NO_LOGIN,
            fullname=self.user.fullname
        )
        assert_true(mail.send_mail())

    def test_no_addon_callback(self):
        mail = mails.QueuedMail()
        mail.create(
            to_addr=self.user.username,
            send_at=datetime.utcnow(),
            user=self.user,
            mail=mails.NO_ADDON,
            fullname=self.user.fullname
        )
        assert_true(mail.send_mail())

    def test_new_public_project_callback_for_no_project(self):
        mail = mails.QueuedMail()
        mail.create(
            to_addr=self.user.username,
            send_at=datetime.utcnow(),
            user=self.user,
            mail=mails.NEW_PUBLIC_PROJECT,
            fullname=self.user.fullname,
            project_title='Oh noes',
            nid='',
        )
        assert_false(mail.send_mail())

    def test_new_public_project_callback_success(self):
        node = factories.ProjectFactory()
        node.is_public = True
        node.save()
        mail = mails.QueuedMail()
        mail.create(
            to_addr=self.user.username,
            send_at=datetime.utcnow(),
            user=self.user,
            mail=mails.NEW_PUBLIC_PROJECT,
            fullname=self.user.fullname,
            project_title='Oh yass',
            nid=node._id
        )
        assert_true(mail.send_mail())

    def test_welcome_osf4m_callback(self):
        node = factories.ProjectFactory()
        file_node = node.get_addon('osfstorage').root_node
        self.user.date_last_login = datetime.utcnow() - timedelta(days=13)
        self.user.save()
        mail = mails.QueuedMail()
        mail.create(
            to_addr=self.user.username,
            send_at=datetime.utcnow(),
            user=self.user,
            mail=mails.WELCOME_OSF4M,
            fullname=self.user.fullname,
            conference='Kill\'em conference',
            presentation='presentation',
            fid=file_node._id
        )
        assert_true(mail.send_mail())
        assert_equal(mail.data['downloads'], 0)

    def test_same_sent(self):
        user = factories.UserFactory()
        mail = mails.QueuedMail()
        mail.create(
            to_addr=user.username,
            send_at=datetime.utcnow(),
            user=user,
            mail=mails.NO_ADDON,
            fullname=user.fullname
        )
        assert_equal(len(mail.find_same_sent()), 0)
        mail.send_mail()
        assert_equal(len(mail.find_same_sent()), 1)
