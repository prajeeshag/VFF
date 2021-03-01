import rules


@rules.predicate
def is_club_manager(user, obj):
    if not obj:
        return False
    return (rules.test_rule('can_manage_club', user, obj.home) or
            rules.test_rule('can_manage_club', user, obj.away))


is_match_manager = rules.is_group_member('match_managers')
is_director = rules.is_group_member('directors')
member_of_club_managers = rules.is_group_member('club_admins')

rules.set_rule('enter_match_details', is_match_manager |
               is_director | is_club_manager)
rules.set_rule('manage_match_menu', is_match_manager |
               is_director | member_of_club_managers)
