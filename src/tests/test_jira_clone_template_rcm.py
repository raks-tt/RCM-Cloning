import unittest

from cloner.jira_clone_template_rcm import extract_fields, create_parser


class TestJiraCloneTemplate(unittest.TestCase):

    def test_extra_fields(self):
        """Test that fields are extracted to dict properly."""
        parser = create_parser()
        input = ["--pav", "spam-1.0",
                 "--keywords", "bicycle, repair, man",
                 "--label", "Red Leicester, Tilsit, Emmental",
                 "--assignee", "Mr. Creosote",
                 "--reporter", "Brian",
                 "--milestone", "nudge"]
        args = parser.parse_args(input)
        fields = extract_fields(args)
        expected = {
            "PAV": "spam-1.0",
            "keywords": ["bicycle", "repair", "man"],
            "labels": ["Red Leicester", "Tilsit", "Emmental"],
            "assignee": "Mr. Creosote",
            "reporter": "Brian",
            "milestone": "nudge"
        }
        self.assertEqual(fields, expected)


if __name__ == '__main__':
    unittest.main()
