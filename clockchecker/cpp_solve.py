from __future__ import annotations

import ctypes
from ctypes import c_int8, c_uint8, c_int16, c_int, Structure, POINTER, byref
import enum
import os
import subprocess
from typing import Iterator

from . import core
from . import characters
from . import events
from . import info
from .core import Puzzle, State, StateGen


MAX_PLAYERS = 16
MAX_NIGHTS = 10
MAX_SCRIPT = 64
MAX_INFO_NODES = 512
MAX_EVENTS_PER_DAY = 16
MAX_DEATHS_PER_NIGHT = 16
MAX_EXTERNAL_PER_SLOT = 16
MAX_SOLUTIONS = 4096

NONE_PLAYER = -1


class CategoryBit(enum.IntFlag):
    CAT_NONE = 0
    CAT_TOWNSFOLK = 1 << 0
    CAT_OUTSIDER = 1 << 1
    CAT_MINION = 1 << 2
    CAT_DEMON = 1 << 3
    CAT_TRAVELLER = 1 << 4


CATEGORY_TO_BIT = {
    characters.Townsfolk: CategoryBit.CAT_TOWNSFOLK,
    characters.Outsider: CategoryBit.CAT_OUTSIDER,
    characters.Minion: CategoryBit.CAT_MINION,
    characters.Demon: CategoryBit.CAT_DEMON,
    characters.Traveller: CategoryBit.CAT_TRAVELLER,
}

# Exact same order as enum CharacterID in clockchecker.hpp
CHARACTER_LIST: list[type[characters.Character] | None] = [
    None,
    characters.Acrobat,
    characters.AlHadikhia,
    characters.Alsaahir,
    characters.Artist,
    characters.Atheist,
    characters.Balloonist,
    characters.Baron,
    characters.Boffin,
    characters.Butler,
    characters.Cerenovus,
    characters.Chambermaid,
    characters.Chef,
    characters.Clockmaker,
    characters.Courtier,
    characters.DevilsAdvocate,
    characters.Dreamer,
    characters.Drunk,
    characters.Empath,
    characters.EvilTwin,
    characters.Exorcist,
    characters.FangGu,
    characters.Flowergirl,
    characters.FortuneTeller,
    characters.Gambler,
    characters.Goblin,
    characters.Golem,
    characters.Gossip,
    characters.Hermit,
    characters.Imp,
    characters.Investigator,
    characters.Juggler,
    characters.Kazali,
    characters.Klutz,
    characters.Knight,
    characters.Leviathan,
    characters.Librarian,
    characters.LordOfTyphon,
    characters.Lunatic,
    characters.Marionette,
    characters.Mathematician,
    characters.Mayor,
    characters.Monk,
    characters.Mutant,
    characters.NightWatchman,
    characters.NoDashii,
    characters.Noble,
    characters.Oracle,
    characters.Philosopher,
    characters.PitHag,
    characters.Po,
    characters.Poisoner,
    characters.Politician,
    characters.PoppyGrower,
    characters.Princess,
    characters.Professor,
    characters.Progidy,
    characters.Pukka,
    characters.Puzzlemaster,
    characters.Ravenkeeper,
    characters.Recluse,
    characters.Riot,
    characters.Sage,
    characters.Saint,
    characters.Savant,
    characters.ScarletWoman,
    characters.Seamstress,
    characters.Shabaloth,
    characters.Shugenja,
    characters.Slayer,
    characters.SnakeCharmer,
    characters.Soldier,
    characters.Spy,
    characters.Steward,
    characters.Sweetheart,
    characters.TeaLady,
    characters.TownCrier,
    characters.Undertaker,
    characters.Vigormortis,
    characters.VillageIdiot,
    characters.Virgin,
    characters.Vortox,
    characters.Washerwoman,
    characters.Widow,
    characters.Witch,
    characters.Xaan,
    characters.Zombuul,
]

CHAR_COUNT = len(CHARACTER_LIST)
CHAR_TO_ID: dict[type[characters.Character] | None, int] = {
    cls: idx for idx, cls in enumerate(CHARACTER_LIST)
}


class AttrID(enum.IntEnum):
    ATTR_NONE = 0
    ATTR_RED_HERRING = enum.auto()
    ATTR_SELF_DROISON = enum.auto()
    ATTR_TARGET = enum.auto()
    ATTR_PUZZLE_DRUNK = enum.auto()
    ATTR_SPENT = enum.auto()


class InfoType(enum.IntEnum):
    INFO_NONE = 0
    INFO_OP_OR = enum.auto()
    INFO_OP_AND = enum.auto()
    INFO_OP_XOR = enum.auto()
    INFO_OP_EQ = enum.auto()
    INFO_OP_INVERT = enum.auto()
    INFO_IS_EVIL = enum.auto()
    INFO_IS_DROISONED = enum.auto()
    INFO_IS_ALIVE = enum.auto()
    INFO_IS_CHARACTER = enum.auto()
    INFO_IS_CATEGORY = enum.auto()
    INFO_CHAR_ATTR_EQ = enum.auto()
    INFO_PLAYER_ATTR_EQ = enum.auto()
    INFO_EXACTLY_N = enum.auto()
    INFO_IS_IN_PLAY = enum.auto()
    INFO_DRUNK_BETWEEN_TOWNSFOLK = enum.auto()
    INFO_LONGEST_ROW_OF_TOWNSFOLK = enum.auto()
    INFO_WIDOW_POISONED = enum.auto()
    INFO_CHARACTER_TYPES_AMONG_PLAYERS = enum.auto()
    INFO_CHARACTER_IS_NEXT_TO_CHARACTER = enum.auto()
    PING_ARTIST = enum.auto()
    PING_SAVANT = enum.auto()
    PING_CHEF = enum.auto()
    PING_CLOCKMAKER = enum.auto()
    PING_CHAMBERMAID = enum.auto()
    PING_DREAMER = enum.auto()
    PING_EMPATH = enum.auto()
    PING_FLOWERGIRL = enum.auto()
    PING_FORTUNE_TELLER = enum.auto()
    PING_INVESTIGATOR = enum.auto()
    PING_JUGGLER = enum.auto()
    PING_KNIGHT = enum.auto()
    PING_LIBRARIAN = enum.auto()
    PING_MATHEMATICIAN = enum.auto()
    PING_NOBLE = enum.auto()
    PING_ORACLE = enum.auto()
    PING_PRODIGY = enum.auto()
    PING_PUZZLEMASTER = enum.auto()
    PING_RAVENKEEPER = enum.auto()
    PING_SAGE = enum.auto()
    PING_SEAMSTRESS = enum.auto()
    PING_SHUGENJA = enum.auto()
    PING_STEWARD = enum.auto()
    PING_TOWN_CRIER = enum.auto()
    PING_UNDERTAKER = enum.auto()
    PING_VILLAGE_IDIOT = enum.auto()
    PING_WASHERWOMAN = enum.auto()
    NOTINFO_BALLOONIST_PING = enum.auto()
    NOTINFO_CHARACTER_CHANGE = enum.auto()
    NOTINFO_ACROBAT_CHOICE = enum.auto()
    NOTINFO_COURTIER_CHOICE = enum.auto()
    NOTINFO_EXORCIST_CHOICE = enum.auto()
    NOTINFO_GAMBLER_GAMBLE = enum.auto()
    NOTINFO_MONK_CHOICE = enum.auto()
    NOTINFO_NIGHTWATCHMAN_CHOICE = enum.auto()
    NOTINFO_PHILOSOPHER_CHOICE = enum.auto()
    NOTINFO_SNAKECHARMER_CHOICE = enum.auto()
    EXTINFO_CERENOVUS_MAD = enum.auto()
    EXTINFO_EVILTWIN_IS = enum.auto()
    EXTINFO_NIGHTWATCHMAN_PING = enum.auto()
    EXTINFO_POPPYGROWER_IN_PLAY = enum.auto()
    EXTINFO_WIDOW_IN_PLAY = enum.auto()


class EventType(enum.IntEnum):
    EVENT_NONE = 0
    EVENT_EXECUTION = enum.auto()
    EVENT_EXECUTION_BY_ST = enum.auto()
    EVENT_UNEVENTFUL_NOMINATION = enum.auto()
    EVENT_DIES = enum.auto()
    EVENT_DOOMSAYER_CALL = enum.auto()
    EVENT_SLAYER_SHOT = enum.auto()
    EVENT_JUGGLER_JUGGLE = enum.auto()
    EVENT_KLUTZ_CHOICE = enum.auto()
    EVENT_GOSSIP_GOSSIP = enum.auto()
    EVENT_FLOWERGIRL_VOTERS = enum.auto()
    EVENT_TOWNCRIER_NOMINATORS = enum.auto()


class CInfoNode(Structure):
    _fields_ = [
        ("type", c_uint8),
        ("player1", c_int8),
        ("player2", c_int8),
        ("player3", c_int8),
        ("character1", c_uint8),
        ("character2", c_uint8),
        ("category", c_uint8),
        ("flag", c_uint8),
        ("count", c_int16),
        ("min_val", c_int16),
        ("max_val", c_int16),
        ("child_a", c_int16),
        ("child_b", c_int16),
        ("extra_count", c_uint8),
        ("extra_indices", c_int16 * MAX_PLAYERS),
    ]


class CEventNode(Structure):
    _fields_ = [
        ("type", c_uint8),
        ("player", c_int8),
        ("target", c_int8),
        ("flag", c_uint8),
        ("info_node_idx", c_int16),
        ("count", c_uint8),
        ("players", c_int8 * MAX_PLAYERS),
        ("characters", c_uint8 * MAX_PLAYERS),
    ]


class CNightDeathNode(Structure):
    _fields_ = [
        ("player", c_int8),
        ("is_resurrection", c_uint8),
    ]


class CExternalInfoEntry(Structure):
    _fields_ = [
        ("info_node_idx", c_int16),
        ("player_id", c_int8),
    ]


class CSerializedPuzzle(Structure):
    _fields_ = [
        ("num_players", c_uint8),
        ("max_night", c_uint8),
        ("max_day", c_uint8),
        ("finish_final_day", c_uint8),
        ("deduplicate_initial_characters", c_uint8),
        ("allow_duplicate_tokens_in_bag", c_uint8),
        ("player_zero_is_you", c_uint8),
        ("allow_killing_dead_players", c_uint8),
        ("max_speculation", c_int16),
        ("category_counts", c_int16 * 4),
        ("player_claims", c_uint8 * MAX_PLAYERS),
        ("num_demons", c_uint8),
        ("demons", c_uint8 * MAX_SCRIPT),
        ("num_minions", c_uint8),
        ("minions", c_uint8 * MAX_SCRIPT),
        ("num_hidden_good", c_uint8),
        ("hidden_good", c_uint8 * MAX_SCRIPT),
        ("num_hidden_self", c_uint8),
        ("hidden_self", c_uint8 * MAX_SCRIPT),
        ("num_script", c_uint8),
        ("script", c_uint8 * MAX_SCRIPT),
        ("num_setup_order", c_uint8),
        ("setup_order", c_uint8 * MAX_SCRIPT),
        ("num_night_order", c_uint8),
        ("night_order", c_uint8 * MAX_SCRIPT),
        ("num_day_order", c_uint8),
        ("day_order", c_uint8 * MAX_SCRIPT),
        ("num_info_nodes", c_int16),
        ("info_nodes", CInfoNode * MAX_INFO_NODES),
        ("night_info", ((c_int16 * CHAR_COUNT) * MAX_NIGHTS) * MAX_PLAYERS),
        ("day_info", ((c_int16 * CHAR_COUNT) * MAX_NIGHTS) * MAX_PLAYERS),
        ("external_info_count", (c_uint8 * CHAR_COUNT) * MAX_NIGHTS),
        ("external_info", ((CExternalInfoEntry * MAX_EXTERNAL_PER_SLOT) * CHAR_COUNT) * MAX_NIGHTS),
        ("day_event_counts", c_uint8 * MAX_NIGHTS),
        ("day_events", (CEventNode * MAX_EVENTS_PER_DAY) * MAX_NIGHTS),
        ("night_death_counts", c_uint8 * MAX_NIGHTS),
        ("night_deaths", (CNightDeathNode * MAX_DEATHS_PER_NIGHT) * MAX_NIGHTS),
    ]


class CSerializedSolutionPlayer(Structure):
    _fields_ = [
        ("initial_character", c_uint8),
        ("final_character", c_uint8),
        ("drunklike_character", c_uint8),
        ("is_evil", c_uint8),
        ("is_dead", c_uint8),
        ("droison_count", c_int8),
        ("vigormortised", c_uint8),
        ("self_droison", c_uint8),
        ("target", c_int8),
        ("aux_target", c_int8),
        ("history_len", c_uint8),
        ("target_history", c_int8 * MAX_NIGHTS),
    ]


class CSerializedSolution(Structure):
    _fields_ = [
        ("players", CSerializedSolutionPlayer * MAX_PLAYERS),
    ]


_LIB = None


def _get_lib():
    global _LIB
    if _LIB is not None:
        return _LIB

    cpp_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cpp")
    so_path = os.path.join(cpp_dir, "libclockchecker.so")
    src_path = os.path.join(cpp_dir, "solver.cpp")
    hdr_path = os.path.join(cpp_dir, "clockchecker.hpp")

    need_build = not os.path.exists(so_path) or (
        os.path.getmtime(so_path) < max(os.path.getmtime(src_path), os.path.getmtime(hdr_path))
    )
    if need_build:
        subprocess.run(
            ["g++", "-O3", "-shared", "-fPIC", "-std=c++20", src_path, "-o", so_path],
            check=True,
        )

    lib = ctypes.CDLL(so_path)
    lib.get_serialized_puzzle_size.argtypes = []
    lib.get_serialized_puzzle_size.restype = c_int
    lib.get_serialized_solution_size.argtypes = []
    lib.get_serialized_solution_size.restype = c_int

    assert ctypes.sizeof(CSerializedPuzzle) == lib.get_serialized_puzzle_size(), (
        f"Struct size mismatch: Python={ctypes.sizeof(CSerializedPuzzle)} vs C++={lib.get_serialized_puzzle_size()}"
    )
    assert ctypes.sizeof(CSerializedSolution) == lib.get_serialized_solution_size(), (
        f"Solution struct size mismatch: Python={ctypes.sizeof(CSerializedSolution)} vs C++={lib.get_serialized_solution_size()}"
    )

    lib.solve_puzzle_cpp.argtypes = [
        POINTER(CSerializedPuzzle),
        POINTER(CSerializedSolution),
        c_int,
    ]
    lib.solve_puzzle_cpp.restype = c_int
    _LIB = lib
    return _LIB


def _serialize_info_node(cpuzzle: CSerializedPuzzle, item) -> int:
    idx = cpuzzle.num_info_nodes
    assert idx < MAX_INFO_NODES, "Exceeded MAX_INFO_NODES"
    cpuzzle.num_info_nodes += 1
    node = cpuzzle.info_nodes[idx]
    node.player1 = NONE_PLAYER
    node.player2 = NONE_PLAYER
    node.player3 = NONE_PLAYER
    node.character1 = 0
    node.character2 = 0
    node.category = 0
    node.flag = 0
    node.count = 0
    node.min_val = 0
    node.max_val = 0
    node.child_a = -1
    node.child_b = -1
    node.extra_count = 0

    if isinstance(item, info.InfoOp):
        op_map = {
            "or": InfoType.INFO_OP_OR,
            "and": InfoType.INFO_OP_AND,
            "xor": InfoType.INFO_OP_XOR,
            "eq": InfoType.INFO_OP_EQ,
            "invert": InfoType.INFO_OP_INVERT,
        }
        node.type = op_map[item.op]
        node.child_a = _serialize_info_node(cpuzzle, item.a)
        if item.b is not None:
            node.child_b = _serialize_info_node(cpuzzle, item.b)

    elif isinstance(item, info.IsEvil):
        node.type = InfoType.INFO_IS_EVIL
        node.player1 = item.player

    elif isinstance(item, info.IsDroisoned):
        node.type = InfoType.INFO_IS_DROISONED
        node.player1 = item.player

    elif isinstance(item, info.IsAlive):
        node.type = InfoType.INFO_IS_ALIVE
        node.player1 = item.player

    elif isinstance(item, info.IsCharacter):
        node.type = InfoType.INFO_IS_CHARACTER
        node.player1 = item.player
        node.character1 = CHAR_TO_ID[item.character]

    elif isinstance(item, info.IsCategory):
        node.type = InfoType.INFO_IS_CATEGORY
        node.player1 = item.player
        node.category = CATEGORY_TO_BIT[item.category]
        node.flag = int(bool(item.assume_droisoned))

    elif isinstance(item, info.IsInPlay):
        node.type = InfoType.INFO_IS_IN_PLAY
        node.character1 = CHAR_TO_ID[item.character]

    elif isinstance(item, info.ExactlyN):
        node.type = InfoType.INFO_EXACTLY_N
        node.count = item.N
        node.extra_count = len(item.args)
        for i, arg in enumerate(item.args):
            node.extra_indices[i] = _serialize_info_node(cpuzzle, arg)

    elif isinstance(item, info.DrunkBetweenTownsfolk):
        node.type = InfoType.INFO_DRUNK_BETWEEN_TOWNSFOLK

    elif isinstance(item, info.LongestRowOfTownsfolk):
        node.type = InfoType.INFO_LONGEST_ROW_OF_TOWNSFOLK
        if item.length is not None:
            node.flag = 1
            node.count = item.length
        else:
            node.flag = 0
            node.min_val = item.minimum
            node.max_val = item.maximum

    elif isinstance(item, info.CharAttrEq):
        node.type = InfoType.INFO_CHAR_ATTR_EQ
        node.player1 = item.player
        attr_map = {
            "red_herring": AttrID.ATTR_RED_HERRING,
            "self_droison": AttrID.ATTR_SELF_DROISON,
            "target": AttrID.ATTR_TARGET,
            "puzzle_drunk": AttrID.ATTR_PUZZLE_DRUNK,
            "spent": AttrID.ATTR_SPENT,
        }
        if item.attr not in attr_map:
            raise NotImplementedError(f"Unsupported CharAttrEq attr: {item.attr}")
        node.category = attr_map[item.attr]
        if item.attr in ("self_droison", "spent"):
            node.flag = int(bool(item.value))
        else:
            node.player2 = NONE_PLAYER if item.value is None else int(item.value)

    elif isinstance(item, characters.Artist.Ping):
        node.type = InfoType.PING_ARTIST
        node.child_a = _serialize_info_node(cpuzzle, item.statement)

    elif isinstance(item, characters.Savant.Ping):
        node.type = InfoType.PING_SAVANT
        node.child_a = _serialize_info_node(cpuzzle, item.a)
        node.child_b = _serialize_info_node(cpuzzle, item.b)

    elif isinstance(item, characters.Chef.Ping):
        node.type = InfoType.PING_CHEF
        node.count = item.count

    elif isinstance(item, characters.Clockmaker.Ping):
        node.type = InfoType.PING_CLOCKMAKER
        node.count = item.steps

    elif isinstance(item, characters.Chambermaid.Ping):
        node.type = InfoType.PING_CHAMBERMAID
        node.player1 = item.player1
        node.player2 = item.player2
        node.count = item.count

    elif isinstance(item, characters.Dreamer.Ping):
        node.type = InfoType.PING_DREAMER
        node.player1 = item.player
        node.character1 = CHAR_TO_ID[item.character1]
        node.character2 = CHAR_TO_ID[item.character2]

    elif isinstance(item, characters.Empath.Ping):
        node.type = InfoType.PING_EMPATH
        node.count = item.count

    elif isinstance(item, characters.FortuneTeller.Ping):
        node.type = InfoType.PING_FORTUNE_TELLER
        node.player1 = item.player1
        node.player2 = item.player2
        node.flag = int(bool(item.demon))

    elif isinstance(item, characters.Investigator.Ping):
        node.type = InfoType.PING_INVESTIGATOR
        node.player1 = item.player1
        node.player2 = item.player2
        node.character1 = CHAR_TO_ID[item.character]

    elif isinstance(item, characters.Washerwoman.Ping):
        node.type = InfoType.PING_WASHERWOMAN
        node.player1 = item.player1
        node.player2 = item.player2
        node.character1 = CHAR_TO_ID[item.character]

    elif isinstance(item, characters.Librarian.Ping):
        node.type = InfoType.PING_LIBRARIAN
        node.player1 = NONE_PLAYER if item.player1 is None else item.player1
        node.player2 = NONE_PLAYER if item.player2 is None else item.player2
        node.character1 = CHAR_TO_ID[item.character]

    elif isinstance(item, characters.Juggler.Ping):
        node.type = InfoType.PING_JUGGLER
        node.count = item.count

    elif isinstance(item, characters.Knight.Ping):
        node.type = InfoType.PING_KNIGHT
        node.player1 = item.player1
        node.player2 = item.player2

    elif isinstance(item, characters.Mathematician.Ping):
        node.type = InfoType.PING_MATHEMATICIAN
        node.count = item.count

    elif isinstance(item, characters.Noble.Ping):
        node.type = InfoType.PING_NOBLE
        node.player1 = item.player1
        node.player2 = item.player2
        node.player3 = item.player3

    elif isinstance(item, characters.Oracle.Ping):
        node.type = InfoType.PING_ORACLE
        node.count = item.count

    elif isinstance(item, characters.Seamstress.Ping):
        node.type = InfoType.PING_SEAMSTRESS
        node.player1 = item.player1
        node.player2 = item.player2
        node.flag = int(bool(item.same))

    elif isinstance(item, characters.Steward.Ping):
        node.type = InfoType.PING_STEWARD
        node.player1 = item.player

    elif isinstance(item, characters.Undertaker.Ping):
        node.type = InfoType.PING_UNDERTAKER
        node.player1 = NONE_PLAYER if item.player is None else item.player
        node.character1 = CHAR_TO_ID[item.character]

    elif isinstance(item, characters.VillageIdiot.Ping):
        node.type = InfoType.PING_VILLAGE_IDIOT
        node.player1 = item.player
        node.flag = int(bool(item.is_evil))

    elif isinstance(item, characters.Shugenja.Ping):
        node.type = InfoType.PING_SHUGENJA
        node.flag = int(bool(item.clockwise))

    elif isinstance(item, characters.Ravenkeeper.Ping):
        node.type = InfoType.PING_RAVENKEEPER
        node.player1 = item.player
        node.character1 = CHAR_TO_ID[item.character]

    elif isinstance(item, characters.Sage.Ping):
        node.type = InfoType.PING_SAGE
        node.player1 = item.player1
        node.player2 = item.player2

    elif isinstance(item, characters.Puzzlemaster.Ping):
        node.type = InfoType.PING_PUZZLEMASTER
        node.player1 = item.guess
        node.player2 = item.demon

    elif isinstance(item, characters.Balloonist.Ping):
        node.type = InfoType.NOTINFO_BALLOONIST_PING
        node.player1 = item.player

    elif isinstance(item, characters.Acrobat.Choice):
        node.type = InfoType.NOTINFO_ACROBAT_CHOICE
        node.player1 = item.player

    elif isinstance(item, characters.Courtier.Choice):
        node.type = InfoType.NOTINFO_COURTIER_CHOICE
        node.character1 = CHAR_TO_ID[item.character]

    elif isinstance(item, characters.Gambler.Gamble):
        node.type = InfoType.NOTINFO_GAMBLER_GAMBLE
        node.player1 = item.player
        node.character1 = CHAR_TO_ID[item.character]

    elif isinstance(item, characters.Monk.Choice):
        node.type = InfoType.NOTINFO_MONK_CHOICE
        node.player1 = item.player

    elif isinstance(item, characters.SnakeCharmer.Choice):
        node.type = InfoType.NOTINFO_SNAKECHARMER_CHOICE
        node.player1 = item.player

    elif isinstance(item, characters.NightWatchman.Choice):
        node.type = InfoType.NOTINFO_NIGHTWATCHMAN_CHOICE
        node.player1 = item.player

    elif isinstance(item, characters.EvilTwin.Is):
        node.type = InfoType.EXTINFO_EVILTWIN_IS
        node.player1 = item.eviltwin

    elif isinstance(item, characters.NightWatchman.Ping):
        node.type = InfoType.EXTINFO_NIGHTWATCHMAN_PING
        node.player1 = item.player

    elif isinstance(item, characters.Widow.InPlay):
        node.type = InfoType.EXTINFO_WIDOW_IN_PLAY

    elif isinstance(item, info.CharacterChange):
        node.type = InfoType.NOTINFO_CHARACTER_CHANGE
        node.character1 = CHAR_TO_ID[item.character]

    else:
        raise NotImplementedError(f"Unsupported Info/Ping type in C++ serializer: {type(item)}")

    return idx


def serialize_puzzle(puzzle: Puzzle) -> CSerializedPuzzle:
    cp = CSerializedPuzzle()
    N = len(puzzle.players)
    cp.num_players = N
    cp.max_night = puzzle.max_night
    cp.max_day = puzzle.max_day
    cp.finish_final_day = int(bool(puzzle.finish_final_day))
    cp.deduplicate_initial_characters = int(bool(puzzle.deduplicate_initial_characters))
    cp.allow_duplicate_tokens_in_bag = int(bool(puzzle.allow_duplicate_tokens_in_bag))
    cp.player_zero_is_you = int(bool(puzzle.player_zero_is_you))
    cp.allow_killing_dead_players = int(bool(puzzle.allow_killing_dead_players))
    cp.max_speculation = puzzle.compromises.max_speculation

    for i in range(4):
        cp.category_counts[i] = puzzle.category_counts[i]

    for i, p in enumerate(puzzle.players):
        cp.player_claims[i] = CHAR_TO_ID[p.claim]

    def fill_char_array(target_arr, src_list):
        for i, c in enumerate(src_list):
            target_arr[i] = CHAR_TO_ID[c]
        return len(src_list)

    cp.num_demons = fill_char_array(cp.demons, puzzle.demons)
    cp.num_minions = fill_char_array(cp.minions, puzzle.minions)
    cp.num_hidden_good = fill_char_array(cp.hidden_good, puzzle.hidden_good)
    cp.num_hidden_self = fill_char_array(cp.hidden_self, puzzle.hidden_self)
    cp.num_script = fill_char_array(cp.script, puzzle.script)
    cp.num_setup_order = fill_char_array(cp.setup_order, puzzle.setup_order)
    cp.num_night_order = fill_char_array(cp.night_order, puzzle.night_order)
    cp.num_day_order = fill_char_array(cp.day_order, puzzle.day_order)

    # Initialize night_info and day_info lookup tables to -1 (0xFFFF in two's complement)
    ctypes.memset(
        ctypes.addressof(cp) + CSerializedPuzzle.night_info.offset,
        0xFF,
        CSerializedPuzzle.night_info.size,
    )
    ctypes.memset(
        ctypes.addressof(cp) + CSerializedPuzzle.day_info.offset,
        0xFF,
        CSerializedPuzzle.day_info.size,
    )

    cp.num_info_nodes = 0
    for pid in range(N):
        for (night, char_cls), item in puzzle._night_info[pid].items():
            cid = 0 if char_cls is info.CharacterChange else CHAR_TO_ID[char_cls]
            cp.night_info[pid][night][cid] = _serialize_info_node(cp, item)
        for (day, char_cls), item in puzzle._day_info[pid].items():
            cid = CHAR_TO_ID[char_cls]
            cp.day_info[pid][day][cid] = _serialize_info_node(cp, item)

    # External info
    for (char_cls, night), entries in puzzle.external_info_registry.items():
        cid = CHAR_TO_ID[char_cls]
        cp.external_info_count[night][cid] = len(entries)
        for idx, (ext_item, pid) in enumerate(entries):
            cp.external_info[night][cid][idx].info_node_idx = _serialize_info_node(cp, ext_item)
            cp.external_info[night][cid][idx].player_id = pid

    # Day events
    for day, ev_list in puzzle.day_events.items():
        cp.day_event_counts[day] = len(ev_list)
        for idx, ev in enumerate(ev_list):
            cev = cp.day_events[day][idx]
            if isinstance(ev, events.Execution) and not isinstance(ev, events.ExecutionByST):
                cev.type = EventType.EVENT_EXECUTION
                cev.player = ev.player
                cev.flag = int(bool(ev.died))
            elif isinstance(ev, characters.Slayer.Shot):
                cev.type = EventType.EVENT_SLAYER_SHOT
                cev.player = ev.player
                cev.target = ev.target
                cev.flag = int(bool(ev.died))
            elif isinstance(ev, characters.Juggler.Juggle):
                cev.type = EventType.EVENT_JUGGLER_JUGGLE
                cev.player = ev.player
                cev.count = len(ev.juggle)
                for j_idx, (t_pid, t_char) in enumerate(ev.juggle.items()):
                    cev.players[j_idx] = t_pid
                    cev.characters[j_idx] = CHAR_TO_ID[t_char]
            elif isinstance(ev, events.Doomsayer.Call):
                cev.type = EventType.EVENT_DOOMSAYER_CALL
                cev.player = ev.player
                cev.target = ev.died
            elif isinstance(ev, characters.Gossip.Gossip):
                cev.type = EventType.EVENT_GOSSIP_GOSSIP
                cev.player = ev.player
                cev.info_node_idx = _serialize_info_node(cp, ev.statement)
            elif isinstance(ev, characters.Klutz.Choice):
                cev.type = EventType.EVENT_KLUTZ_CHOICE
                cev.player = ev.player
                cev.target = ev.choice
            else:
                raise NotImplementedError(f"Unsupported Day Event in C++ serializer: {type(ev)}")

    # Night deaths
    for night, nd_list in puzzle.night_deaths.items():
        cp.night_death_counts[night] = len(nd_list)
        for idx, nd in enumerate(nd_list):
            cp.night_deaths[night][idx].player = nd.player
            cp.night_deaths[night][idx].is_resurrection = int(isinstance(nd, events.NightResurrection))

    return cp


def _reconstruct_state(puzzle: Puzzle, csol: CSerializedSolution) -> State:
    world = puzzle.state_template.fork()
    N = len(puzzle.players)
    world.initial_characters = tuple(
        CHARACTER_LIST[csol.players[i].initial_character]
        for i in range(N)
    )
    for i in range(N):
        sp = csol.players[i]
        p = world.players[i]
        char_cls = CHARACTER_LIST[sp.final_character]
        p.character = char_cls()
        p.is_evil = bool(sp.is_evil)
        p.is_dead = bool(sp.is_dead)
        p.droison_count = int(sp.droison_count)
        if sp.vigormortised:
            p.character.vigormortised = True
        if sp.self_droison and hasattr(p.character, "self_droison"):
            p.character.self_droison = True
        if sp.drunklike_character != 0:
            p.character.drunklike_character = CHARACTER_LIST[sp.drunklike_character]()
        if isinstance(p.character, characters.FortuneTeller) and sp.target != NONE_PLAYER:
            p.character.red_herring = int(sp.target)
        elif isinstance(p.character, characters.Puzzlemaster) and sp.target != NONE_PLAYER:
            p.character.puzzle_drunk = int(sp.target)
        elif isinstance(p.character, characters.EvilTwin) and sp.target != NONE_PLAYER:
            p.character.twin = int(sp.target)
        elif isinstance(p.character, characters.NoDashii):
            p.character.tf_neighbour_fwd = None if sp.target == NONE_PLAYER else int(sp.target)
            p.character.tf_neighbour_bkwd = None if sp.aux_target == NONE_PLAYER else int(sp.aux_target)
        elif hasattr(p.character, "target"):
            p.character.target = None if sp.target == NONE_PLAYER else int(sp.target)
        if hasattr(p.character, "target_history") and sp.history_len > 0:
            p.character.target_history = [
                int(sp.target_history[h]) for h in range(sp.history_len)
            ]
    return world


def solve_cpp(puzzle: Puzzle) -> StateGen:
    lib = _get_lib()
    cpuzzle = serialize_puzzle(puzzle)
    out_solutions = (CSerializedSolution * MAX_SOLUTIONS)()
    count = lib.solve_puzzle_cpp(byref(cpuzzle), out_solutions, MAX_SOLUTIONS)
    for i in range(count):
        yield _reconstruct_state(puzzle, out_solutions[i])
