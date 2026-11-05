#pragma once

#include <cstdint>
#include <cstring>

namespace clockchecker {

constexpr int MAX_PLAYERS = 16;
constexpr int MAX_NIGHTS = 10;
constexpr int MAX_SCRIPT = 64;
constexpr int MAX_INFO_NODES = 512;
constexpr int MAX_EVENTS_PER_DAY = 16;
constexpr int MAX_DEATHS_PER_NIGHT = 16;
constexpr int MAX_EXTERNAL_PER_SLOT = 16;
constexpr int MAX_STEPS = 256;
constexpr int MAX_SOLUTIONS = 4096;

using PlayerID = int8_t;
constexpr PlayerID NONE_PLAYER = -1;

enum Category : uint8_t {
    CAT_NONE      = 0,
    CAT_TOWNSFOLK = 1 << 0,
    CAT_OUTSIDER  = 1 << 1,
    CAT_MINION    = 1 << 2,
    CAT_DEMON     = 1 << 3,
    CAT_TRAVELLER = 1 << 4,
};

enum WakePattern : uint8_t {
    WAKE_NEVER = 0,
    WAKE_FIRST_NIGHT,
    WAKE_EACH_NIGHT,
    WAKE_EACH_NIGHT_STAR,
    WAKE_EACH_NIGHT_UNTIL_SPENT,
    WAKE_MANUAL,
};

enum Phase : uint8_t {
    PHASE_SETUP = 0,
    PHASE_NIGHT,
    PHASE_DAY,
};

enum Reason : uint8_t {
    REASON_NONE = 0,
    REASON_SETUP,
    REASON_DROISON,
    REASON_UNDROISON,
    REASON_DEATH,
    REASON_RESURRECTION,
    REASON_CHARACTER_CHANGE,
};

enum CallbackType : uint8_t {
    CB_PRE_DEATH = 0,
    CB_POST_DEATH = 1,
    CB_ALIGNMENT_CHANGE = 2,
    CB_CHARACTER_CHANGE = 3,
    CB_COUNT = 4,
};

enum CharacterID : uint8_t {
    CHAR_NONE = 0,
    CHAR_Acrobat,
    CHAR_AlHadikhia,
    CHAR_Alsaahir,
    CHAR_Artist,
    CHAR_Atheist,
    CHAR_Balloonist,
    CHAR_Baron,
    CHAR_Boffin,
    CHAR_Butler,
    CHAR_Cerenovus,
    CHAR_Chambermaid,
    CHAR_Chef,
    CHAR_Clockmaker,
    CHAR_Courtier,
    CHAR_DevilsAdvocate,
    CHAR_Dreamer,
    CHAR_Drunk,
    CHAR_Empath,
    CHAR_EvilTwin,
    CHAR_Exorcist,
    CHAR_FangGu,
    CHAR_Flowergirl,
    CHAR_FortuneTeller,
    CHAR_Gambler,
    CHAR_Goblin,
    CHAR_Golem,
    CHAR_Gossip,
    CHAR_Hermit,
    CHAR_Imp,
    CHAR_Investigator,
    CHAR_Juggler,
    CHAR_Kazali,
    CHAR_Klutz,
    CHAR_Knight,
    CHAR_Leviathan,
    CHAR_Librarian,
    CHAR_LordOfTyphon,
    CHAR_Lunatic,
    CHAR_Marionette,
    CHAR_Mathematician,
    CHAR_Mayor,
    CHAR_Monk,
    CHAR_Mutant,
    CHAR_NightWatchman,
    CHAR_NoDashii,
    CHAR_Noble,
    CHAR_Oracle,
    CHAR_Philosopher,
    CHAR_PitHag,
    CHAR_Po,
    CHAR_Poisoner,
    CHAR_Politician,
    CHAR_PoppyGrower,
    CHAR_Princess,
    CHAR_Professor,
    CHAR_Progidy,
    CHAR_Pukka,
    CHAR_Puzzlemaster,
    CHAR_Ravenkeeper,
    CHAR_Recluse,
    CHAR_Riot,
    CHAR_Sage,
    CHAR_Saint,
    CHAR_Savant,
    CHAR_ScarletWoman,
    CHAR_Seamstress,
    CHAR_Shabaloth,
    CHAR_Shugenja,
    CHAR_Slayer,
    CHAR_SnakeCharmer,
    CHAR_Soldier,
    CHAR_Spy,
    CHAR_Steward,
    CHAR_Sweetheart,
    CHAR_TeaLady,
    CHAR_TownCrier,
    CHAR_Undertaker,
    CHAR_Vigormortis,
    CHAR_VillageIdiot,
    CHAR_Virgin,
    CHAR_Vortox,
    CHAR_Washerwoman,
    CHAR_Widow,
    CHAR_Witch,
    CHAR_Xaan,
    CHAR_Zombuul,
    CHAR_COUNT
};

struct STBool {
    uint8_t bits; // bit 0: truth, bit 1: is_maybe, bit 2: st_says

    constexpr STBool() : bits(0) {}
    constexpr explicit STBool(uint8_t b) : bits(b) {}
    constexpr explicit STBool(bool b) : bits(b ? 0b101 : 0b000) {}
    constexpr STBool(bool truth, bool is_maybe, bool st_says)
        : bits((truth ? 1 : 0) | (is_maybe ? 2 : 0) | (st_says ? 4 : 0)) {}

    // Disallow implicit bool conversion to prevent accidental &&, ||, ! usage
    explicit operator bool() const = delete;

    constexpr bool truth() const { return (bits & 1) != 0; }
    constexpr bool is_maybe() const { return (bits & 2) != 0; }
    constexpr bool st_says() const { return (bits & 4) != 0; }

    constexpr bool is_true() const { return (bits & 0b110) == 0b100; }
    constexpr bool not_true() const { return !is_true(); }

    constexpr bool is_false() const { return (bits & 0b110) == 0b000; }
    constexpr bool not_false() const { return !is_false(); }

    constexpr bool st_lying() const { return truth() != st_says(); }
    constexpr bool exact_eq(STBool other) const { return bits == other.bits; }

    constexpr STBool operator|(STBool other) const {
        bool t = truth() || other.truth();
        bool s = st_says() || other.st_says();
        bool m = (is_true() || other.is_true()) ? false : (is_maybe() || other.is_maybe());
        return STBool(t, m, s);
    }
    constexpr STBool& operator|=(STBool other) {
        *this = *this | other;
        return *this;
    }

    constexpr STBool operator&(STBool other) const {
        bool t = truth() && other.truth();
        bool s = st_says() && other.st_says();
        bool m = (is_false() || other.is_false()) ? false : (is_maybe() || other.is_maybe());
        return STBool(t, m, s);
    }
    constexpr STBool& operator&=(STBool other) {
        *this = *this & other;
        return *this;
    }

    constexpr STBool operator==(STBool other) const {
        return STBool(
            truth() == other.truth(),
            is_maybe() || other.is_maybe(),
            st_says() == other.st_says()
        );
    }

    constexpr STBool operator^(STBool other) const {
        return STBool(
            truth() != other.truth(),
            is_maybe() || other.is_maybe(),
            st_says() != other.st_says()
        );
    }

    constexpr STBool operator~() const {
        return STBool(!truth(), is_maybe(), !st_says());
    }
};

namespace STBoolVal {
    constexpr STBool FALSE       = STBool(false, false, false);
    constexpr STBool FALSE_MAYBE = STBool(false, true,  false);
    constexpr STBool FALSE_LYING = STBool(true,  false, false);
    constexpr STBool TRUE        = STBool(true,  false, true);
    constexpr STBool TRUE_MAYBE  = STBool(true,  true,  true);
    constexpr STBool TRUE_LYING  = STBool(false, false, true);
}

enum AttrID : uint8_t {
    ATTR_NONE = 0,
    ATTR_RED_HERRING,
    ATTR_SELF_DROISON,
    ATTR_TARGET,
    ATTR_PUZZLE_DRUNK,
    ATTR_SPENT,
};

enum InfoType : uint8_t {
    INFO_NONE = 0,
    // Logical operators (InfoOp)
    INFO_OP_OR,
    INFO_OP_AND,
    INFO_OP_XOR,
    INFO_OP_EQ,
    INFO_OP_INVERT,
    // Core Info primitives
    INFO_IS_EVIL,
    INFO_IS_DROISONED,
    INFO_IS_ALIVE,
    INFO_IS_CHARACTER,
    INFO_IS_CATEGORY,
    INFO_CHAR_ATTR_EQ,
    INFO_PLAYER_ATTR_EQ,
    INFO_EXACTLY_N,
    INFO_IS_IN_PLAY,
    // Puzzle-specific Info
    INFO_DRUNK_BETWEEN_TOWNSFOLK,
    INFO_LONGEST_ROW_OF_TOWNSFOLK,
    INFO_WIDOW_POISONED,
    INFO_CHARACTER_TYPES_AMONG_PLAYERS,
    INFO_CHARACTER_IS_NEXT_TO_CHARACTER,
    // Character Pings (Info subclasses)
    PING_ARTIST,
    PING_SAVANT,
    PING_CHEF,
    PING_CLOCKMAKER,
    PING_CHAMBERMAID,
    PING_DREAMER,
    PING_EMPATH,
    PING_FLOWERGIRL,
    PING_FORTUNE_TELLER,
    PING_INVESTIGATOR,
    PING_JUGGLER,
    PING_KNIGHT,
    PING_LIBRARIAN,
    PING_MATHEMATICIAN,
    PING_NOBLE,
    PING_ORACLE,
    PING_PRODIGY,
    PING_PUZZLEMASTER,
    PING_RAVENKEEPER,
    PING_SAGE,
    PING_SEAMSTRESS,
    PING_SHUGENJA,
    PING_STEWARD,
    PING_TOWN_CRIER,
    PING_UNDERTAKER,
    PING_VILLAGE_IDIOT,
    PING_WASHERWOMAN,
    // NotInfo (choices / special pings stored in night_info)
    NOTINFO_BALLOONIST_PING,
    NOTINFO_CHARACTER_CHANGE,
    NOTINFO_ACROBAT_CHOICE,
    NOTINFO_COURTIER_CHOICE,
    NOTINFO_EXORCIST_CHOICE,
    NOTINFO_GAMBLER_GAMBLE,
    NOTINFO_MONK_CHOICE,
    NOTINFO_NIGHTWATCHMAN_CHOICE,
    NOTINFO_PHILOSOPHER_CHOICE,
    NOTINFO_SNAKECHARMER_CHOICE,
    // ExternalInfo
    EXTINFO_CERENOVUS_MAD,
    EXTINFO_EVILTWIN_IS,
    EXTINFO_NIGHTWATCHMAN_PING,
    EXTINFO_POPPYGROWER_IN_PLAY,
    EXTINFO_WIDOW_IN_PLAY,
};

struct InfoNode {
    InfoType type;
    PlayerID player1;
    PlayerID player2;
    PlayerID player3;
    CharacterID character1;
    CharacterID character2;
    uint8_t category;      // Category bitflag
    uint8_t flag;          // bool flag (e.g. assume_droisoned, demon, same, clockwise, is_evil)
    int16_t count;         // N, steps, count, length
    int16_t min_val;
    int16_t max_val;
    int16_t child_a;       // index into SerializedPuzzle::info_nodes, or -1
    int16_t child_b;       // index into SerializedPuzzle::info_nodes, or -1
    uint8_t extra_count;
    int16_t extra_indices[MAX_PLAYERS];
};

enum EventType : uint8_t {
    EVENT_NONE = 0,
    EVENT_EXECUTION,
    EVENT_EXECUTION_BY_ST,
    EVENT_UNEVENTFUL_NOMINATION,
    EVENT_DIES,
    EVENT_DOOMSAYER_CALL,
    EVENT_SLAYER_SHOT,
    EVENT_JUGGLER_JUGGLE,
    EVENT_KLUTZ_CHOICE,
    EVENT_GOSSIP_GOSSIP,
    EVENT_FLOWERGIRL_VOTERS,
    EVENT_TOWNCRIER_NOMINATORS,
};

struct EventNode {
    EventType type;
    PlayerID player;
    PlayerID target;
    uint8_t flag;          // died or after_nominating
    int16_t info_node_idx; // for Gossip
    uint8_t count;
    PlayerID players[MAX_PLAYERS];
    CharacterID characters[MAX_PLAYERS];
};

struct NightDeathNode {
    PlayerID player;
    uint8_t is_resurrection;
};

struct ExternalInfoEntry {
    int16_t info_node_idx;
    PlayerID player_id;
};

struct SerializedPuzzle {
    uint8_t num_players;
    uint8_t max_night;
    uint8_t max_day;
    uint8_t finish_final_day;
    uint8_t deduplicate_initial_characters;
    uint8_t allow_duplicate_tokens_in_bag;
    uint8_t player_zero_is_you;
    uint8_t allow_killing_dead_players;
    int16_t max_speculation;

    int16_t category_counts[4]; // T, O, M, D

    CharacterID player_claims[MAX_PLAYERS];

    uint8_t num_demons;
    CharacterID demons[MAX_SCRIPT];

    uint8_t num_minions;
    CharacterID minions[MAX_SCRIPT];

    uint8_t num_hidden_good;
    CharacterID hidden_good[MAX_SCRIPT];

    uint8_t num_hidden_self;
    CharacterID hidden_self[MAX_SCRIPT];

    uint8_t num_script;
    CharacterID script[MAX_SCRIPT];

    uint8_t num_setup_order;
    CharacterID setup_order[MAX_SCRIPT];

    uint8_t num_night_order;
    CharacterID night_order[MAX_SCRIPT];

    uint8_t num_day_order;
    CharacterID day_order[MAX_SCRIPT];

    int16_t num_info_nodes;
    InfoNode info_nodes[MAX_INFO_NODES];

    // Indexed by [player][night][character_id] -> info_node_idx (-1 if none)
    int16_t night_info[MAX_PLAYERS][MAX_NIGHTS][CHAR_COUNT];
    // Indexed by [player][day][character_id] -> info_node_idx (-1 if none)
    int16_t day_info[MAX_PLAYERS][MAX_NIGHTS][CHAR_COUNT];

    // External info registry: indexed by [night][character_id]
    uint8_t external_info_count[MAX_NIGHTS][CHAR_COUNT];
    ExternalInfoEntry external_info[MAX_NIGHTS][CHAR_COUNT][MAX_EXTERNAL_PER_SLOT];

    // Day events: indexed by [day]
    uint8_t day_event_counts[MAX_NIGHTS];
    EventNode day_events[MAX_NIGHTS][MAX_EVENTS_PER_DAY];

    // Night deaths: indexed by [night]
    uint8_t night_death_counts[MAX_NIGHTS];
    NightDeathNode night_deaths[MAX_NIGHTS][MAX_DEATHS_PER_NIGHT];
};

struct AbilityInstance {
    CharacterID type = CHAR_NONE;
    uint8_t first_night = 1;
    PlayerID ability_src = NONE_PLAYER;
    bool effects_active = false;
    bool spent = false;
    bool has_spent_attr = false;
    bool vigormortised = false;
    bool self_droison = false;

    PlayerID target = NONE_PLAYER;
    PlayerID aux_target = NONE_PLAYER;
    uint8_t prev_category = 0;
    uint8_t prev_regs_mask = 0;
    int8_t choice_night = -1;
    bool aux_bool = false;
    uint16_t aux_mask = 0;
};

struct Player {
    PlayerID id = 0;
    CharacterID claim = CHAR_NONE;
    AbilityInstance character;
    AbilityInstance drunklike_char;
    bool has_drunklike_char = false;

    bool is_evil = false;
    bool is_dead = false;
    bool woke_tonight = false;
    int8_t droison_count = 0;
    bool ever_behaved_evil = false;

    bool speculative_evil = false;
    bool speculative_good = false;
    bool speculative_ceremad = false;

    uint8_t safe_from_demon_count = 0;
    uint8_t safe_from_execution = 0;
    uint8_t exorcised_count = 0;
    uint8_t ceremad = 0;
    PlayerID witch_cursed = NONE_PLAYER;

    uint8_t num_juggles = 0;
    STBool correct_juggles[8];

    STBool saved_day_bool;
    int8_t saved_day_num = -1;

    uint8_t protection_map[MAX_PLAYERS];

    uint8_t history_len = 0;
    PlayerID target_history[MAX_NIGHTS];
};

struct State {
    const SerializedPuzzle* puzzle = nullptr;
    Player players[MAX_PLAYERS];
    CharacterID initial_characters[MAX_PLAYERS];

    Phase current_phase = PHASE_SETUP;
    uint8_t phase_order_index = 0;
    int8_t night = 0; // 0 means None
    int8_t day = 0;   // 0 means None

    CharacterID currently_acting_character = CHAR_NONE;
    uint8_t num_players_still_to_act = 0;
    PlayerID players_still_to_act[MAX_PLAYERS];

    uint16_t previously_alive_mask = 0;
    int16_t math_misreg_bounds[2] = {0, 0};
    uint16_t math_misregisterers_mask = 0;
    uint16_t tomorrow_math_misreg_mask = 0;

    uint16_t character_callbacks[CB_COUNT] = {0, 0, 0, 0};

    bool vortox = false;
    bool fanggu_already_jumped = false;
    bool cull_branch = false;
    uint8_t active_princesses = 0;
    uint8_t rioting_count = 0;
    PlayerID pithag_preventing_kills = NONE_PLAYER;
    PlayerID pithag_kills_at_night_end = NONE_PLAYER;
    int8_t widow_pinged_night = -1;
};

struct SerializedSolutionPlayer {
    CharacterID initial_character;
    CharacterID final_character;
    CharacterID drunklike_character;
    uint8_t is_evil;
    uint8_t is_dead;
    int8_t droison_count;
    uint8_t vigormortised;
    uint8_t self_droison;
    PlayerID target;
    PlayerID aux_target;
    uint8_t history_len;
    PlayerID target_history[MAX_NIGHTS];
};

struct SerializedSolution {
    SerializedSolutionPlayer players[MAX_PLAYERS];
};

} // namespace clockchecker

extern "C" {
    int solve_puzzle_cpp(
        const clockchecker::SerializedPuzzle* puzzle,
        clockchecker::SerializedSolution* out_solutions,
        int max_solutions
    );
    int get_serialized_puzzle_size();
    int get_serialized_solution_size();
}
