"""Enumerations for the Dark Forest simulation."""

from enum import Enum, auto


class Strategy(str, Enum):
    """Civilization survival strategy."""
    HIDER = 'hider'
    AGGRESSOR = 'aggressor'
    DIPLOMAT = 'diplomat'
    OBSERVER = 'observer'
    CLEANER = 'cleaner'

    @property
    def label(self) -> str:
        return {
            Strategy.HIDER: '隐藏者',
            Strategy.AGGRESSOR: '侵略者',
            Strategy.DIPLOMAT: '外交家',
            Strategy.OBSERVER: '观察者',
            Strategy.CLEANER: '清理者',
        }[self]


class Action(str, Enum):
    """Actions a civilization can take each turn."""
    HIDE = 'hide'
    EXPAND = 'expand'
    RESEARCH = 'research'
    DETECT = 'detect'
    BROADCAST_SELF = 'broadcast_self'
    BROADCAST_TARGET = 'broadcast_target'
    ATTACK = 'attack'
    COMMUNICATE = 'communicate'
    PROPOSE_TREATY = 'propose_treaty'
    BREAK_TREATY = 'break_treaty'
    DECLARE_DETERRENCE = 'declare_deterrence'
    NOTHING = 'nothing'


class CivState(str, Enum):
    """Civilization diplomatic/military state."""
    PEACEFUL = 'peaceful'
    ALERT = 'alert'
    DETERRED = 'deterred'
    AT_WAR = 'at_war'
    ALLIED = 'allied'


class WeaponType(str, Enum):
    CONVENTIONAL = 'conventional'
    PHOTOID = 'photoid'
    DUAL_VECTOR_FOIL = 'dual_vector_foil'

    @property
    def label(self) -> str:
        return {
            WeaponType.CONVENTIONAL: '常规打击',
            WeaponType.PHOTOID: '光粒',
            WeaponType.DUAL_VECTOR_FOIL: '二向箔',
        }[self]


class TreatyType(str, Enum):
    NON_AGGRESSION = 'non_aggression'
    ALLIANCE = 'alliance'
    TRADE = 'trade'

    @property
    def label(self) -> str:
        return {
            TreatyType.NON_AGGRESSION: '互不侵犯条约',
            TreatyType.ALLIANCE: '军事同盟',
            TreatyType.TRADE: '贸易协定',
        }[self]
