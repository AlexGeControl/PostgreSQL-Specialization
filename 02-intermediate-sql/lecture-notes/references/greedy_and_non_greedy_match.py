import re

# greedy matching pattern
greedy_match_pattern = r'a.*b'
# non-greedy matching pattern
non_greedy_match_pattern = r'a.*?b'

# test string
test_string = 'a123b456b789'

# find the first match using greedy matching
greedy_match = re.search(pattern=greedy_match_pattern, string=test_string)
# find the frist match using non-greedy matching
non_greedy_match = re.search(pattern=non_greedy_match_pattern, string=test_string)

# check results
assert greedy_match is not None, "Greedy match failed"
assert greedy_match.group() == 'a123b456b', "Greedy match did not return expected result"

assert non_greedy_match is not None, "Non-greedy match failed"
assert non_greedy_match.group() == 'a123b', "Non-greedy match did not return expected result"

# Output:
# Greedy Matches: 'a123b456b'
# Non-Greedy Matches: 'a123b'
# Explanation:
# In the greedy match, the pattern 'a.*b' matches from the first 'a' to the last 'b', capturing everything in between.
# In the non-greedy match, the pattern 'a.*?b' captures the shortest possible string between 'a' and 'b', resulting in two matches.