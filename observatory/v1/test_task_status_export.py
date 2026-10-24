"""Step C: pending task export is read-only and colors never invent activity."""
import hashlib
import json
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import patch
import uuid

from store import Store, stage
from test_v1 import v2_event
from task_intents import TaskIntents, task_display, session_overview
import repo_viewer_export as export


class StatusExportTests(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory(prefix='fortis-status-export-')
        self.addCleanup(tmp.cleanup)
        self.root=Path(tmp.name);self.inbox=self.root/'inbox';self.inbox.mkdir()
        self.store=Store(self.root/'archive',{'repo':self.inbox})
        self.meta=self.store.register('https://chatgpt.com/c/12345678-abcd','repo','Synthetic')
        self.sid=self.meta['reporting_session_id'];self.api=TaskIntents(self.store)
        self.key=self.api.issue_key(self.sid,self.meta['conversation_id']);self.seq=0

    def draft(self):
        body={'version':1,'reporting_session_id':self.sid,'conversation_id':self.meta['conversation_id'],
              'task_id':'task_'+uuid.uuid4().hex,'prepared_at_client_ms':int(time.time()*1000)-1000}
        self.api.register(body,self.key);return body

    def send(self,body):
        self.api.send_state({k:body[k] for k in ('version','reporting_session_id','conversation_id','task_id')} | {
            'revision':1,'phase':'send_unconfirmed','observed_at_client_ms':int(time.time()*1000)},self.key)

    def accept(self,body,name):
        stage(self.inbox,v2_event(self.meta,body['task_id'],self.seq,name));self.seq+=1
        self.assertEqual(self.store.poll()['accepted'],1)

    def state(self):return {'ok':True,'sessions':self.store.sessions()}

    def hashes(self):
        return {str(p.relative_to(self.root)):hashlib.sha256(p.read_bytes()).hexdigest()
                for p in self.root.rglob('*') if p.is_file()}

    def test_draft_is_listed_before_events_without_original_or_write_side_effects(self):
        draft=self.draft();before=self.hashes()
        cards=export.session_tasks(self.sid,self.state(),self.root)
        self.assertEqual(cards['task_ids'],[draft['task_id']])
        card=cards['tasks'][0]
        self.assertTrue(cards['task_status_available']);self.assertEqual(card['state'],'prepared')
        self.assertIsNone(card['status_color']);self.assertFalse(card['original_received'])
        self.assertIsNone(card['original_preview']);self.assertIsNotNone(card['first_seen_at'])
        self.assertEqual(before,self.hashes())
        self.assertEqual(self.store.sessions()[0]['events_count'],0)

    def test_mixed_states_keep_working_pending_draft_failed_and_blocked_counts(self):
        working=self.draft();waiting1=self.draft();waiting2=self.draft();draft=self.draft()
        completed=self.draft();failed=self.draft();blocked=self.draft()
        self.accept(working,'progress');self.send(waiting1);self.send(waiting2)
        self.accept(completed,'completed');self.accept(failed,'failed');self.accept(blocked,'blocked')
        cards=export.session_tasks(self.sid,self.state(),self.root)
        by_id={t['task_id']:t for t in cards['tasks']};overview=cards['task_overview']
        self.assertEqual((overview['primary_color'],overview['working_count'],overview['pending_count']),(None,1,2))
        self.assertEqual((overview['draft_count'],overview['failed_count'],overview['blocked_count'],overview['completed_count']),(1,1,1,1))
        self.assertEqual(by_id[failed['task_id']]['status_color'],'red')
        self.assertEqual(by_id[completed['task_id']]['status_color'],'green')
        self.assertIsNone(by_id[draft['task_id']]['status_color'])
        self.assertIsNone(by_id[blocked['task_id']]['status_color'])
        self.assertEqual(len(by_id),7)
        self.assertEqual(overview['primary_state'],'blocked')
        self.assertEqual(overview['version'],2)

    def test_user_marker_is_waiting_not_blue_and_silence_never_red(self):
        draft=self.draft();self.accept(draft,'user_message')
        cards=export.session_tasks(self.sid,self.state(),self.root)
        self.assertEqual(cards['tasks'][0]['status_color'],'yellow')
        self.assertEqual(cards['task_overview']['pending_count'],1)
        self.accept(draft,'started')
        with patch('task_intents.time.time',return_value=time.time()+86400):
            card=export.session_tasks(self.sid,self.state(),self.root)['tasks'][0]
        self.assertEqual(card['status_color'],'purple');self.assertEqual(card['state'],'unknown')
        self.assertIsNone(card['terminal_event'])

    def test_corrupted_intent_is_explicit_but_does_not_hide_old_history(self):
        draft=self.draft();self.accept(draft,'started')
        path=self.api._folder(self.sid)/(draft['task_id']+'.md');path.write_text('corrupted')
        cards=export.session_tasks(self.sid,self.state(),self.root)
        self.assertFalse(cards['task_status_available']);self.assertEqual(cards['task_ids'],[draft['task_id']])
        self.assertFalse(cards['task_overview']['available']);self.assertIsNone(cards['tasks'][0]['status_color'])

    def test_owner_state_summary_works_with_legacy_api_and_excludes_private_fields(self):
        draft=self.draft();self.send(draft);state=self.state();before=self.hashes()
        with patch('repo_viewer_export.DEFAULT_ROOT',self.root),patch('repo_viewer_export.api_call',return_value=state) as api:
            out=export.read_only('state')
            api.assert_called_once_with(self.root,export.DEFAULT_PORT,'/api/state')
        self.assertEqual(out['sessions'][0]['state'],state['sessions'][0]['state'])
        overview=out['sessions'][0]['task_overview'];self.assertEqual(overview['pending_count'],1)
        encoded=json.dumps(overview)
        for private in (self.key,'original_text','submitted_text','summary','observer_key','message_writer_key'):
            self.assertNotIn(private,encoded)
        self.assertEqual(before,self.hashes())
        with patch('repo_viewer_export.DEFAULT_ROOT',self.root),patch('repo_viewer_export.api_call',return_value=state):
            out=export.read_only('tasks',self.sid)
        self.assertEqual(out['task_ids'],[draft['task_id']])

    def test_missing_local_archive_never_created_and_no_false_status(self):
        missing=self.root/'never-created';snapshot,overview=export.lifecycle(self.sid,missing)
        self.assertIsNone(snapshot);self.assertFalse(overview['available']);self.assertFalse(missing.exists())

    def test_pending_completion_race_and_bounded_cards(self):
        done=self.draft();self.accept(done,'completed');self.send(done);pending=self.draft()
        cards=export.session_tasks(self.sid,self.state(),self.root)
        self.assertEqual(cards['task_overview']['primary_state'],'prepared')
        self.assertIsNone(cards['task_overview']['primary_color'])
        self.assertEqual(cards['task_overview']['completed_count'],1)
        with patch('repo_viewer_export.MAX_TASK_CARDS',1):
            cards=export.session_tasks(self.sid,self.state(),self.root)
        self.assertTrue(cards['truncated']);self.assertEqual(len(cards['tasks']),1)

    def test_old_silence_late_progress_and_failure_never_override_latest_completed(self):
        old=self.draft();self.accept(old,'started')
        latest=self.draft();self.accept(latest,'completed')
        with patch('task_intents.time.time',return_value=time.time()+86400):
            cards=export.session_tasks(self.sid,self.state(),self.root)
        self.assertEqual(cards['task_overview']['primary_state'],'completed')
        self.assertEqual(cards['task_overview']['primary_color'],'green')
        self.assertEqual({t['task_id']:t for t in cards['tasks']}[old['task_id']]['state'],'unknown')
        for late in ('progress','failed'):
            self.accept(old,late)
            cards=export.session_tasks(self.sid,self.state(),self.root)
            self.assertEqual(cards['task_overview']['primary_state'],'completed')
            self.assertEqual(cards['tasks'][-1]['task_id'],latest['task_id'])
        self.assertEqual({t['task_id']:t for t in cards['tasks']}[old['task_id']]['status_color'],'red')

    def test_latest_draft_and_pending_override_older_work_without_starting_activity(self):
        old=self.draft();self.accept(old,'progress')
        latest=self.draft()
        cards=export.session_tasks(self.sid,self.state(),self.root)
        self.assertEqual(cards['task_overview']['primary_state'],'prepared')
        self.assertIsNone(cards['task_overview']['primary_color'])
        self.send(latest)
        cards=export.session_tasks(self.sid,self.state(),self.root)
        self.assertEqual(cards['task_overview']['primary_state'],'waiting_ai')
        self.assertEqual(cards['task_overview']['primary_color'],'yellow')
        with patch('task_intents.time.time',return_value=time.time()+86400):
            overview=session_overview(self.api.snapshot(self.sid))
        self.assertEqual(overview['primary_state'],'waiting_ai')
        self.assertIn('длительное ожидание',overview['primary_label'])
        self.assertNotEqual(overview['primary_color'],'red')

    def test_offline_old_intent_registered_late_does_not_become_current(self):
        latest=self.draft();self.accept(latest,'completed')
        delayed={**latest,'task_id':'task_'+uuid.uuid4().hex,
                 'prepared_at_client_ms':latest['prepared_at_client_ms']-10000}
        self.api.register(delayed,self.key)
        cards=export.session_tasks(self.sid,self.state(),self.root)
        self.assertEqual(cards['task_overview']['primary_state'],'completed')
        self.assertEqual(cards['tasks'][-1]['task_id'],latest['task_id'])
        self.assertEqual(cards['task_overview']['basis'],'latest_task')

    def test_legacy_task_order_uses_first_event_not_latest_event(self):
        old={'task_id':'task_'+uuid.uuid4().hex};new={'task_id':'task_'+uuid.uuid4().hex}
        self.accept(old,'started');self.accept(new,'completed');self.accept(old,'progress')
        cards=export.session_tasks(self.sid,self.state(),self.root)
        self.assertEqual(cards['task_overview']['primary_state'],'completed')
        self.assertEqual(cards['tasks'][-1]['task_id'],new['task_id'])

    def test_palette_has_no_gray_unknown_input_cannot_inject_a_color(self):
        for state,color in [('prepared',None),('waiting_ai','yellow'),('working','blue'),
                            ('silent','purple'),('unknown','purple'),('completed','green'),
                            ('failed','red'),('blocked',None),('<script>',None)]:
            self.assertEqual(task_display({'state':state})['status_color'],color)
        snapshot=self.api.snapshot(self.sid);overview=session_overview(snapshot)
        self.assertIsNone(overview['primary_color']);self.assertEqual(overview['pending_count'],0)


if __name__=='__main__':unittest.main()
