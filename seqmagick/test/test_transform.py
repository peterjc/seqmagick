"""
Tests for seqmagick.transform
"""

import unittest

from Bio import Alphabet
from Bio.SeqRecord import SeqRecord
from Bio.Seq import Seq

from seqmagick import transform

def _alignment_record(sequence):
    return SeqRecord(Seq(sequence,
        alphabet=Alphabet.Gapped(Alphabet.generic_dna)))

def seqrecord(sequence_id, sequence_text, alphabet=None):
    """
    Quick shortcut to make a SeqRecord
    """
    return SeqRecord(Seq(sequence_text, alphabet), id=sequence_id)


class PatternReplaceTestCase(unittest.TestCase):

    def create_sequences(self):
        return [
    seqrecord('test_sequence_1', 'ACTGT'),
    seqrecord('test_REPLACE_2', 'ACTGT'),
    seqrecord('other_sequence', 'ATGAG'),
    ]

    def setUp(self):
        super(PatternReplaceTestCase, self).setUp()
        self.sequences = self.create_sequences()

    def tearDown(self):
        super(PatternReplaceTestCase, self).tearDown()

    def test_pattern_replace_none(self):
        result = transform.name_replace(self.sequences, 'ZZZ', 'MATCH')
        result = list(result)
        self.assertEqual(self.sequences, result)

    def test_pattern_replace_static(self):
        result = transform.name_replace(self.sequences, '_REPLACE_',
                '_DONE_')
        result = list(result)
        expected = self.create_sequences()
        expected[1].id = 'test_DONE_2'
        self.assertEqual(self.sequences, result)

    def test_pattern_replace_case_insensitive(self):
        """
        Substitutions are case insensitive
        """
        result = transform.name_replace(self.sequences, '_replace_',
                '_DONE_')
        result = list(result)
        expected = self.create_sequences()
        expected[1].id = 'test_DONE_2'
        self.assertEqual(self.sequences, result)

    def test_pattern_replace_group(self):
        """
        Make sure capturing groups work
        """
        result = transform.name_replace(self.sequences, '_(repl)ace_',
                '_DONE-\\1_')
        result = list(result)
        expected = self.create_sequences()
        expected[1].id = 'test_DONE-repl_2'
        self.assertEqual(self.sequences, result)

class SqueezeTestCase(unittest.TestCase):

    def setUp(self):
        super(SqueezeTestCase, self).setUp()

        self.sequences = [
            seqrecord('sequence_1', 'AC-G--'),
            seqrecord('sequence_2', '-C-GT-'),
            seqrecord('sequence_3', '-T-AG-'),
        ]

    def test_basic_squeeze(self):
        result = list(transform.squeeze(self.sequences,
            [False, False, True, False, False, True]))

        self.assertEqual([4, 4, 4], [len(i) for i in result])
        self.assertEqual([i.id for i in self.sequences], [i.id for i in result])
        expected = [
            seqrecord('sequence_1', 'ACG-'),
            seqrecord('sequence_2', '-CGT'),
            seqrecord('sequence_3', '-TAG'),
        ]

        self.assertEqual([str(i.seq) for i in expected],
                [str(i.seq) for i in result])

class SeqPatternTestCase(unittest.TestCase):

    def setUp(self):
        super(SeqPatternTestCase, self).setUp()

        self.sequences = [
            seqrecord('sequence_1', 'AC-G--'),
            seqrecord('sequence_2', '-C-GT-'),
            seqrecord('sequence_3', '-T-AG-'),
        ]

        self.tests = [('^$', []), ('.*', self.sequences),
                ('^AC', [self.sequences[0]])]

    def test_include(self):
        result = transform.seq_include(self.sequences, '^$')

        for regex, expected in self.tests:
            result = list(transform.seq_include(self.sequences, regex))
            self.assertEqual(expected, result)

    def test_exclude(self):
        result = transform.seq_include(self.sequences, '^$')

        for regex, expected_include in self.tests:
            expected = [i for i in self.sequences if i not in expected_include]
            result = list(transform.seq_exclude(self.sequences, regex))
            self.assertEqual(expected, result)


class HeadTestCase(unittest.TestCase):
    """
    Test for transform.head
    """

    def setUp(self):
        self.sequences = [seqrecord('sequence{0}'.format(i), 'A'*(i+1))
                          for i in xrange(100)]

    def test_zero(self):
        result = list(transform.head(self.sequences, 0))
        self.assertEquals([], result)

    def test_more_seqs_than_available(self):
        """
        Specifying more sequences than are in input records should return
        them all
        """
        result = list(transform.head(self.sequences, 10000))
        self.assertEquals(self.sequences, result)

    def test_values(self):
        """
        Try specifying some values.
        """
        for h in xrange(len(self.sequences) + 1):
            result = list(transform.head(self.sequences, h))
            self.assertEquals(h, len(result))
            self.assertEquals(self.sequences[:h], result)





class IsolateRegionTestCase(unittest.TestCase):

    def setUp(self):
        self.sequences = [_alignment_record('--A--ACTGGACGTATTC-CCCC'),
                          _alignment_record('--AGCACTGGA---ATTC-CCCC')]

    def test_no_isolation(self):
        result = list(transform.isolate_region(self.sequences, 0,
            len(self.sequences[0])))

        self.assertEquals(self.sequences, result)

    def test_single_loc(self):
        start = 2
        end = 3
        result = list(transform.isolate_region(self.sequences, start, end))
        for seq in result:
            self.assertEqual('--A--------------------', str(seq.seq))

    def test_middle(self):
        expected = ['--A--ACTGGA------------', '--AGCACTGGA------------']
        start = 1
        end = 11

        actual = list(transform.isolate_region(self.sequences, start, end))
        actual = [str(s.seq) for s in actual]
        self.assertEquals(expected, actual)

    def test_invalid(self):
        self.assertRaises(ValueError, transform.isolate_region(
                self.sequences, 5, 5).next)
        self.assertRaises(ValueError, transform.isolate_region(
                self.sequences, 10, 5).next)

class MinUngapLengthTestCase(unittest.TestCase):

    def setUp(self):
        self.sequences = [_alignment_record('--AAC--'),
                          _alignment_record('AAAA---'),
                          _alignment_record('-------'),
                          _alignment_record('ACGRAGT')]

    def test_none_pass(self):
        result = list(transform.min_ungap_length_discard(self.sequences, 8))
        self.assertEquals([], result)

    def test_all_pass(self):
        result = list(transform.min_ungap_length_discard(self.sequences, 0))
        self.assertEquals(self.sequences, result)

    def test_partial(self):
        result = transform.min_ungap_length_discard(self.sequences, 4)
        self.assertEquals([self.sequences[1], self.sequences[3]], list(result))

