import datetime
from unittest import TestCase
from datetime import datetime

from src.rhpy import Rhpy


class TestRhpy(TestCase):
    def test__parse_planning_str(self):
        r = Rhpy._parse_planning_str('John Doe', 'Congés payés le 07/10/2022')
        self.assertEqual(r, ('John Doe', 'cp', datetime.strptime('07/10/2022', '%d/%m/%Y'), datetime.strptime('07/10/2022', '%d/%m/%Y')) )

        r = Rhpy._parse_planning_str('John Doe', 'Congés payés du 07/09/2022 au 19/09/2022')
        self.assertEqual(r, ('John Doe', 'cp', datetime.strptime('07/09/2022', '%d/%m/%Y'), datetime.strptime('19/09/2022', '%d/%m/%Y')) )

        r = Rhpy._parse_planning_str('John Doe', 'Télétravail du 26/09/2022 au 27/09/2022')
        self.assertEqual(r, ('John Doe', 'tt', datetime.strptime('26/09/2022', '%d/%m/%Y'), datetime.strptime('27/09/2022', '%d/%m/%Y')) )

    def test__clean_name(self):
        r = Rhpy._clean_name('TAMATORO Johng Ay')
        self.assertEqual(r, ('TAMATORO', 'Johng Ay'))

        r = Rhpy._clean_name('DO PACO Camille' )
        self.assertEqual(r, ('DO PACO', 'Camille'))

        r = Rhpy._clean_name('LAWSON Anthony (0014545)')
        self.assertEqual(r, ('LAWSON', 'Anthony'))

        r = Rhpy._clean_name('NGUYEN Hong Thai (0014547)')
        self.assertEqual(r, ('NGUYEN', 'Hong Thai'))

