import rules


@rules.predicate
def is_club_manager(user, obj):
    if not obj:
        return False
    return obj.user == user


@rules.predicate
def is_playerprofile_owner(user, obj):
    if not obj:
        return False
    if obj.user:
        return user == obj.user
    elif obj.get_club():
        return rules.test_rule('manage_club', user, obj.get_club())


rules.add_rule('manage_club', is_club_manager)
rules.add_rule('manage_profile', is_playerprofile_owner)
rules.add_rule('is_a_club_admin', rules.is_group_member('club_admins'))
