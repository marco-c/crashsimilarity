def structural_word_distance(w1, w2):
    parts1 = w1.split('::')
    parts2 = w2.split('::')
    if len(parts1) < len(parts2):
        return structural_word_distance(w2, w1)
    prefix = 0
    while prefix < len(parts2) and parts1[prefix] == parts2[prefix]:
        prefix += 1
    return 1 - float(prefix) / max(len(parts1), len(parts2))


def edit_distance(s1, s2, ins_cost=lambda a, b: 1, del_cost=lambda a, b: 1, subst_cost=lambda a, b: 1):
    if len(s1) < len(s2):
        return edit_distance(s2, s1, ins_cost, del_cost, subst_cost)

    if len(s2) == 0:
        return len(s1)

    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + ins_cost(s1[i], s2[j])
            deletions = current_row[j] + del_cost(s2[j], s2[j - 1])
            substitutions = previous_row[j] + (c1 != c2) * subst_cost(c1, c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row

    return previous_row[-1]


def edit_distance_structural(trace1, trace2):
    return edit_distance(trace1, trace2, structural_word_distance, structural_word_distance, structural_word_distance)
