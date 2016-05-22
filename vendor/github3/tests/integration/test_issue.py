"""Integration tests for Issues."""
import github3

from .helper import IntegrationHelper


class TestIssue(IntegrationHelper):

    """Integration tests for methods on the Issue class."""

    def test_add_labels(self):
        """Test the ability to add a label to an issue."""
        self.token_login()
        cassette_name = self.cassette_name('add_labels')
        with self.recorder.use_cassette(cassette_name):
            issue = self.gh.issue(username='sigmavirus24',
                                  repository='github3.py',
                                  number=497)

            labels = issue.add_labels('in progress')

        assert len(labels) > 0
        for label in labels:
            assert isinstance(label, github3.issues.issue.Label)

    def test_assign(self):
        """Test the ability to assign a user to an issue."""
        self.token_login()
        cassette_name = self.cassette_name('assign')
        with self.recorder.use_cassette(cassette_name):
            issue = self.gh.issue(username='sigmavirus24',
                                  repository='github3.py',
                                  number=497)
            assigned = issue.assign('itsmemattchung')

        assert assigned is True

    def test_comment(self):
        """Test the ability to retrieve an issue comment."""
        cassette_name = self.cassette_name('comment')
        with self.recorder.use_cassette(cassette_name):
            issue = self.gh.issue(username='sigmavirus24',
                                  repository='github3.py',
                                  number=497)
            comment = issue.comment('165547512')

        assert isinstance(comment, github3.issues.issue.IssueComment)

    def test_comments(self):
        """Test the ability to retrieve comments on an issue."""
        cassette_name = self.cassette_name('comments')
        with self.recorder.use_cassette(cassette_name):
            issue = self.gh.issue('sigmavirus24', 'github3.py', 187)
            assert issue is not None
            comments = list(issue.comments())

        assert len(comments) > 0
        for comment in comments:
            assert isinstance(comment, github3.issues.comment.IssueComment)

    def test_closed(self):
        """Test the ability to close an issue."""
        self.token_login()
        cassette_name = self.cassette_name('closed')
        with self.recorder.use_cassette(cassette_name):
            issue = self.gh.issue(username='sigmavirus24',
                                  repository='github3.py',
                                  number=509)

            closed = issue.close()

        assert closed is True

    def test_create_comment(self):
        """Test the ability to create a comment on an issue."""
        self.token_login()
        cassette_name = self.cassette_name('create_comment')
        with self.recorder.use_cassette(cassette_name):
            issue = self.gh.issue(username='sigmavirus24',
                                  repository='github3.py',
                                  number=509)

            comment = issue.create_comment(
                body='Comment from integration test'
            )

        assert isinstance(comment, github3.issues.issue.IssueComment)

    def test_edit(self):
        """Test the ability to edit an issue."""
        self.token_login()
        cassette_name = self.cassette_name('edit')
        with self.recorder.use_cassette(cassette_name):
            issue = self.gh.issue(username='sigmavirus24',
                                  repository='github3.py',
                                  number=509)
            edited = issue.edit(title='Integration test for editing an issue')

        assert edited is True

    def test_events(self):
        """Test the ability to iterate over issue events."""
        self.token_login()
        cassette_name = self.cassette_name('events')
        with self.recorder.use_cassette(cassette_name):
            repository = self.gh.repository('sigmavirus24', 'github3.py')
            issue = repository.issue(218)
            for event in issue.events():
                assert isinstance(event, github3.issues.event.IssueEvent)
                assert event.issue is None
                assert isinstance(event.actor, github3.users.User)

    def test_labels(self):
        """Test the ability to iterate over issue labels."""
        cassette_name = self.cassette_name('labels')
        with self.recorder.use_cassette(cassette_name):
            issue = self.gh.issue('sigmavirus24', 'github3.py', 187)
            assert issue is not None
            for label in issue.labels():
                assert isinstance(label, github3.issues.label.Label)

    def test_lock(self):
        """Test the ability to lock an issue."""
        self.token_login()
        cassette_name = self.cassette_name('lock')
        with self.recorder.use_cassette(cassette_name):
            issue = self.gh.issue(username='adrianmoisey',
                                  repository='temptest',
                                  number=1)
            locked = issue.lock()

        assert locked is True

    def test_pull_request(self):
        """Test the ability to retrieve the PR associated with an issue."""
        cassette_name = self.cassette_name('pull_request')
        with self.recorder.use_cassette(cassette_name):
            issue = self.gh.issue('sigmavirus24', 'github3.py', 301)
            assert issue is not None
            pull_request = issue.pull_request()

        assert isinstance(pull_request, github3.pulls.PullRequest)

    def test_remove_all_labels(self):
        """Test the ability to remove all labels from an issue."""
        self.token_login()
        cassette_name = self.cassette_name('remove_all_labels')
        with self.recorder.use_cassette(cassette_name):
            issue = self.gh.issue(username='sigmavirus24',
                                  repository='github3.py',
                                  number=509)
            labels = issue.remove_all_labels()

        assert len(labels) == 0

    def test_reopen(self):
        """Test the ability to reopen an issue."""
        self.token_login()
        cassette_name = self.cassette_name('reopen')
        with self.recorder.use_cassette(cassette_name):
            issue = self.gh.issue(username='sigmavirus24',
                                  repository='github3.py',
                                  number=509)
            reopened = issue.reopen()

        assert reopened is True

    def test_remove_label(self):
        """Test the ability to remove a label from an issue."""
        self.token_login()
        cassette_name = self.cassette_name('remove_label')
        with self.recorder.use_cassette(cassette_name):
            issue = self.gh.issue(username='sigmavirus24',
                                  repository='github3.py',
                                  number=509)
            labels = issue.remove_label('in progress')

        assert len(labels) > 0
        for label in labels:
            assert isinstance(label, github3.issues.issue.Label)

    def test_replace_labels(self):
        """Test the ability to replace labels from an issue."""
        self.token_login()
        cassette_name = self.cassette_name('replace_labels')
        with self.recorder.use_cassette(cassette_name):
            issue = self.gh.issue(username='sigmavirus24',
                                  repository='github3.py',
                                  number=509)
            labels = ['in progress', 'easy']
            replaced_labels = issue.replace_labels(labels)

        assert len(replaced_labels) == len(labels)
        for replaced_label in replaced_labels:
            assert isinstance(replaced_label, github3.issues.issue.Label)

    def test_unlock(self):
        """Test the ability to lock an issue."""
        self.token_login()
        cassette_name = self.cassette_name('unlock')
        with self.recorder.use_cassette(cassette_name):
            issue = self.gh.issue(username='adrianmoisey',
                                  repository='temptest',
                                  number=1)
            unlocked = issue.unlock()

        assert unlocked is True


class TestLabel(IntegrationHelper):
    """Integration test for methods on Label class."""

    def test_delete(self):
        """Test the ability to delete a label."""
        self.token_login()
        cassette_name = self.cassette_name('delete')
        with self.recorder.use_cassette(cassette_name):
            repository = self.gh.repository('itsmemattchung', 'github3.py')
            label = repository.label('deleteme')
            assert label.delete()

    def test_update(self):
        """Test the ability to update a label."""
        self.token_login()
        cassette_name = self.cassette_name('update')
        with self.recorder.use_cassette(cassette_name):
            repository = self.gh.repository('itsmemattchung', 'github3.py')
            label = repository.label('integration')
            assert label.update('integration', '5319e7')