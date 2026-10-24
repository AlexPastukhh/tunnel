"""Step D: read-only session summary through the existing observer route."""
import json
from pathlib import Path
import re
import unittest
import uuid

import test_task_intents as fixtures
from task_intents import TaskIntents, session_overview
from store import stage
from test_v1 import v2_event


class ObserverOverviewTests(unittest.TestCase):
    setUp=fixtures.IntentHttpTests.setUp
    request=fixtures.IntentHttpTests.request

    def get(self,key=None,sid=None):
        return self.request('GET','/api/observer-status?session='+(sid or self.sid),
                            headers={'X-Fortis-Observer-Key':key or self.app.store.observer_key(self.sid)})

    def test_draft_and_waiting_counts_share_the_owner_classifier_without_activity(self):
        intents=TaskIntents(self.app.store);intents.register(self.body,self.key)
        code,data=self.get();self.assertEqual(code,200)
        self.assertEqual(data['task_overview'],session_overview(intents.snapshot(self.sid)) | {
            'checked_at_unix':data['task_overview']['checked_at_unix']})
        self.assertIsNone(data['task_overview']['primary_color']);self.assertEqual(data['event'],'none')
        self.assertEqual(data['task_overview']['draft_count'],1)
        send={k:self.body[k] for k in ('version','reporting_session_id','conversation_id','task_id')} | {
            'revision':1,'phase':'send_unconfirmed','observed_at_client_ms':self.body['prepared_at_client_ms']}
        intents.send_state(send,self.key)
        _,data=self.get();self.assertEqual(data['task_overview']['primary_color'],'yellow')
        self.assertEqual(data['task_overview']['pending_count'],1);self.assertEqual(data['event'],'none')
        activity=self.app.store.task_activity(self.sid,self.app.store.observer_key(self.sid),self.body['task_id'])
        self.assertFalse(activity['found'])
        encoded=json.dumps(data['task_overview'])
        for value in (self.key,self.body['task_id'],'original_text','summary','message_writer_key','observer_key'):
            self.assertNotIn(value,encoded)

    def test_key_scope_and_current_routes_do_not_gain_owner_or_write_access(self):
        observer=self.app.store.observer_key(self.sid)
        other=self.app.store.register('https://chatgpt.com/c/other-chat-12345678','repo','Other')
        self.assertEqual(self.get(observer,other['reporting_session_id'])[0],403)
        for key in (self.key,self.app.store.message_writer_key(self.sid),'invalid'):
            self.assertEqual(self.get(key)[0],403)
        self.assertEqual(self.request('GET','/api/task-intents?session='+self.sid,
            headers={'X-Fortis-Observer-Key':observer})[0],401)
        self.assertEqual(self.request(body=self.body,headers={'X-Fortis-Task-Intent-Key':observer})[0],403)

    def test_legacy_event_fields_survive_a_corrupted_intent_snapshot(self):
        intents=TaskIntents(self.app.store);intents.register(self.body,self.key)
        stage(self.app.store.inboxes['repo'],v2_event(self.meta,self.body['task_id'],0,'progress'))
        self.assertEqual(self.app.store.poll()['accepted'],1)
        (intents._folder(self.sid)/(self.body['task_id']+'.md')).write_text('corrupted')
        code,data=self.get();self.assertEqual(code,200);self.assertEqual(data['event'],'progress')
        self.assertFalse(data['task_overview']['available'])
        self.assertNotIn('corrupted',json.dumps(data))

    def test_palette_hex_matches_viewer_and_no_new_bridge_route_is_required(self):
        base=Path(__file__).parent
        js=base.parents[2]/'tabnotifier-fileautosend-autochat'/'src'/'task-favicon.js'
        if not js.exists():self.skipTest('Sibling Notifier checkout unavailable')
        source=js.read_text();viewer=(base/'owner_viewer.py').read_text()
        for color in ('yellow','blue','purple','green','red'):
            code=re.search(r"\b"+color+r": '(#[0-9a-f]{6})'",source).group(1)
            self.assertIn('[data-status="'+color+'"]{--status-color:'+code+'}',viewer)
        bridge=(base/'owner_notifier_bridge.py').read_text()
        self.assertIn('/api/observer-status',bridge)


if __name__=='__main__':unittest.main()
