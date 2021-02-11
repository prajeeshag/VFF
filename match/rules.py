import rules


@rules.predicate
def is_club_manager(user, obj):
    if not obj:
        return False
    return rules.test_rule('manage_club', user, obj.club)


is_match_manager = rules.is_group_member('match_managers')
is_director = rules.is_group_member('directors')

can_add_squad = is_club_manager | is_director | is_match_manager

rules.add_rule('can_add_squad', can_add_squad)
rules.add_rule('can_add_goal', is_match_manager | is_director)
rules.add_rule('can_add_sub', is_match_manager | is_director)
rules.add_rule('can_add_cards', is_match_manager | is_director)
