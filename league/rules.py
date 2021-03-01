import rules

is_match_manager = rules.is_group_member('match_managers')
is_director = rules.is_group_member('directors')
is_league_executive = rules.is_group_member('league_executives')
can_manage_profiles = rules.is_group_member('can_manage_profiles')

rules.set_rule('manage_match', is_match_manager | is_director)
rules.set_rule('manage_profiles', is_league_executive |
               is_director | can_manage_profiles)
