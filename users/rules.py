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


@rules.predicate
def is_player_removeable(user, player):
    if not user.is_authenticated:
        return False
    club = user.get_club()
    if not rules.test_rule('manage_club', user, club):
        return False
    if club.playercount.count <= club.playercount.MIN_NUM_PLAYERS:
        return False
    if not player:
        return False
    if player.user:
        return False
    if club != player.get_club():
        return False
    return True


@rules.predicate
def can_end_contract(user, player):
    if not user.is_authenticated:
        return False
    club = user.get_club()
    if not rules.test_rule('manage_club', user, club):
        return False
    if not player.user:
        return False
    if not player:
        return False
    if club != player.get_club():
        return False
    return True


@rules.predicate
def end_contract_sent(club, player):
    if club.endcontract.filter(player=player).exists():
        return True
    return False


rules.add_rule('manage_club', is_club_manager)
rules.add_rule('manage_profile', is_playerprofile_owner)
rules.add_rule('is_a_club_admin', rules.is_group_member('club_admins'))
rules.add_rule('is_player_removeable', is_player_removeable)
rules.add_rule('can_end_contract', can_end_contract)
rules.add_rule('end_contract_sent', end_contract_sent)
