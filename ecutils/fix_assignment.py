"""
We had two versions of stimulus order (& colors assignment): A and B.
7 participants had version set to "A" in OFL and "B" in DE.
This meant that while blue square was associated with shock in OFL, the yellow
one was marked with "1" (representing CS+) during DE.

Run check_order.py to see inferred versions of OFL and DE for participants.

Here we provide a function to reverse marker - stimulus assignment.
"""


def fix_assignment(code, df):
    """Exchanges direct CS+ and CS- for select subjects to fix an error
    made during stimulus presentation. Works in place."""

    x = ['ZDHMKH', 'QISPNY', 'GDLETK', 'RAZVAJ', 'MQPCWH', 'FFOTFO', 'NKCTEC']
    if code in x:
        for i in df.index:
            if df.loc[i, 'stimulus'] == 'direct CS+':
                df.loc[i, 'stimulus'] = 'direct CS-'
            elif df.loc[i, 'stimulus'] == 'direct CS-':
                df.loc[i, 'stimulus'] = 'direct CS+'
