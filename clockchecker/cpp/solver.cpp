#include "clockchecker.hpp"
#include <algorithm>
#include <vector>

namespace clockchecker {

struct CharMeta {
    Category category;
    WakePattern wake_pattern;
    uint8_t misregister_categories;
    bool lies_about_character_and_info;
    bool is_drunklike;
    bool has_spent;
    uint8_t callbacks_mask;
};

static constexpr CharMeta make_meta(
    Category cat,
    WakePattern wake = WAKE_NEVER,
    uint8_t misreg = 0,
    bool lies = false,
    bool drunklike = false,
    bool spent = false,
    uint8_t cbs = 0
) {
    return CharMeta{cat, wake, misreg, lies, drunklike, spent, cbs};
}

static constexpr CharMeta CHAR_META[CHAR_COUNT] = {
    /* CHAR_NONE */           make_meta(CAT_NONE),
    /* CHAR_Acrobat */        make_meta(CAT_TOWNSFOLK, WAKE_EACH_NIGHT_STAR),
    /* CHAR_AlHadikhia */     make_meta(CAT_DEMON, WAKE_EACH_NIGHT_STAR),
    /* CHAR_Alsaahir */       make_meta(CAT_TOWNSFOLK, WAKE_NEVER),
    /* CHAR_Artist */         make_meta(CAT_TOWNSFOLK, WAKE_NEVER, 0, false, false, true),
    /* CHAR_Atheist */        make_meta(CAT_TOWNSFOLK, WAKE_NEVER),
    /* CHAR_Balloonist */     make_meta(CAT_TOWNSFOLK, WAKE_EACH_NIGHT),
    /* CHAR_Baron */          make_meta(CAT_MINION, WAKE_NEVER),
    /* CHAR_Boffin */         make_meta(CAT_MINION, WAKE_FIRST_NIGHT),
    /* CHAR_Butler */         make_meta(CAT_OUTSIDER, WAKE_EACH_NIGHT),
    /* CHAR_Cerenovus */      make_meta(CAT_MINION, WAKE_EACH_NIGHT),
    /* CHAR_Chambermaid */    make_meta(CAT_TOWNSFOLK, WAKE_EACH_NIGHT),
    /* CHAR_Chef */           make_meta(CAT_TOWNSFOLK, WAKE_FIRST_NIGHT),
    /* CHAR_Clockmaker */     make_meta(CAT_TOWNSFOLK, WAKE_FIRST_NIGHT),
    /* CHAR_Courtier */       make_meta(CAT_TOWNSFOLK, WAKE_EACH_NIGHT_UNTIL_SPENT, 0, false, false, true),
    /* CHAR_DevilsAdvocate */ make_meta(CAT_MINION, WAKE_EACH_NIGHT),
    /* CHAR_Dreamer */        make_meta(CAT_TOWNSFOLK, WAKE_EACH_NIGHT),
    /* CHAR_Drunk */          make_meta(CAT_OUTSIDER, WAKE_MANUAL, 0, true, true, false),
    /* CHAR_Empath */         make_meta(CAT_TOWNSFOLK, WAKE_EACH_NIGHT),
    /* CHAR_EvilTwin */       make_meta(CAT_MINION, WAKE_NEVER, 0, false, false, false, (1 << CB_PRE_DEATH)),
    /* CHAR_Exorcist */       make_meta(CAT_TOWNSFOLK, WAKE_EACH_NIGHT_STAR),
    /* CHAR_FangGu */         make_meta(CAT_DEMON, WAKE_EACH_NIGHT_STAR),
    /* CHAR_Flowergirl */     make_meta(CAT_TOWNSFOLK, WAKE_EACH_NIGHT_STAR),
    /* CHAR_FortuneTeller */  make_meta(CAT_TOWNSFOLK, WAKE_EACH_NIGHT),
    /* CHAR_Gambler */        make_meta(CAT_TOWNSFOLK, WAKE_EACH_NIGHT_STAR),
    /* CHAR_Goblin */         make_meta(CAT_MINION, WAKE_NEVER),
    /* CHAR_Golem */          make_meta(CAT_OUTSIDER, WAKE_NEVER, 0, false, false, true),
    /* CHAR_Gossip */         make_meta(CAT_TOWNSFOLK, WAKE_NEVER),
    /* CHAR_Hermit */         make_meta(CAT_OUTSIDER, WAKE_MANUAL),
    /* CHAR_Imp */            make_meta(CAT_DEMON, WAKE_EACH_NIGHT_STAR),
    /* CHAR_Investigator */   make_meta(CAT_TOWNSFOLK, WAKE_FIRST_NIGHT),
    /* CHAR_Juggler */        make_meta(CAT_TOWNSFOLK, WAKE_MANUAL),
    /* CHAR_Kazali */         make_meta(CAT_DEMON, WAKE_EACH_NIGHT_STAR),
    /* CHAR_Klutz */          make_meta(CAT_OUTSIDER, WAKE_NEVER),
    /* CHAR_Knight */         make_meta(CAT_TOWNSFOLK, WAKE_FIRST_NIGHT),
    /* CHAR_Leviathan */      make_meta(CAT_DEMON, WAKE_NEVER),
    /* CHAR_Librarian */      make_meta(CAT_TOWNSFOLK, WAKE_FIRST_NIGHT),
    /* CHAR_LordOfTyphon */   make_meta(CAT_DEMON, WAKE_EACH_NIGHT_STAR),
    /* CHAR_Lunatic */        make_meta(CAT_OUTSIDER, WAKE_MANUAL, 0, true, true, false),
    /* CHAR_Marionette */     make_meta(CAT_MINION, WAKE_MANUAL, 0, true, true, false),
    /* CHAR_Mathematician */  make_meta(CAT_TOWNSFOLK, WAKE_EACH_NIGHT),
    /* CHAR_Mayor */          make_meta(CAT_TOWNSFOLK, WAKE_NEVER),
    /* CHAR_Monk */           make_meta(CAT_TOWNSFOLK, WAKE_EACH_NIGHT_STAR),
    /* CHAR_Mutant */         make_meta(CAT_OUTSIDER, WAKE_NEVER, 0, true, false, false),
    /* CHAR_NightWatchman */  make_meta(CAT_TOWNSFOLK, WAKE_EACH_NIGHT_UNTIL_SPENT, 0, false, false, true),
    /* CHAR_NoDashii */       make_meta(CAT_DEMON, WAKE_EACH_NIGHT_STAR, 0, false, false, false, (1 << CB_CHARACTER_CHANGE)),
    /* CHAR_Noble */          make_meta(CAT_TOWNSFOLK, WAKE_FIRST_NIGHT),
    /* CHAR_Oracle */         make_meta(CAT_TOWNSFOLK, WAKE_EACH_NIGHT_STAR),
    /* CHAR_Philosopher */    make_meta(CAT_TOWNSFOLK, WAKE_EACH_NIGHT),
    /* CHAR_PitHag */         make_meta(CAT_MINION, WAKE_EACH_NIGHT_STAR),
    /* CHAR_Po */             make_meta(CAT_DEMON, WAKE_EACH_NIGHT_STAR),
    /* CHAR_Poisoner */       make_meta(CAT_MINION, WAKE_EACH_NIGHT),
    /* CHAR_Politician */     make_meta(CAT_OUTSIDER, WAKE_NEVER, 0, true, false, false),
    /* CHAR_PoppyGrower */    make_meta(CAT_TOWNSFOLK, WAKE_NEVER),
    /* CHAR_Princess */       make_meta(CAT_TOWNSFOLK, WAKE_NEVER),
    /* CHAR_Professor */      make_meta(CAT_TOWNSFOLK, WAKE_EACH_NIGHT_STAR),
    /* CHAR_Progidy */        make_meta(CAT_TOWNSFOLK, WAKE_EACH_NIGHT),
    /* CHAR_Pukka */          make_meta(CAT_DEMON, WAKE_EACH_NIGHT),
    /* CHAR_Puzzlemaster */   make_meta(CAT_OUTSIDER, WAKE_NEVER, 0, false, false, true),
    /* CHAR_Ravenkeeper */    make_meta(CAT_TOWNSFOLK, WAKE_MANUAL),
    /* CHAR_Recluse */        make_meta(CAT_OUTSIDER, WAKE_NEVER, CAT_MINION | CAT_DEMON),
    /* CHAR_Riot */           make_meta(CAT_DEMON, WAKE_NEVER),
    /* CHAR_Sage */           make_meta(CAT_TOWNSFOLK, WAKE_MANUAL),
    /* CHAR_Saint */          make_meta(CAT_OUTSIDER, WAKE_NEVER),
    /* CHAR_Savant */         make_meta(CAT_TOWNSFOLK, WAKE_NEVER),
    /* CHAR_ScarletWoman */   make_meta(CAT_MINION, WAKE_MANUAL, 0, false, false, false, (1 << CB_PRE_DEATH)),
    /* CHAR_Seamstress */     make_meta(CAT_TOWNSFOLK, WAKE_EACH_NIGHT_UNTIL_SPENT, 0, false, false, true),
    /* CHAR_Shabaloth */      make_meta(CAT_DEMON, WAKE_EACH_NIGHT_STAR),
    /* CHAR_Shugenja */       make_meta(CAT_TOWNSFOLK, WAKE_FIRST_NIGHT),
    /* CHAR_Slayer */         make_meta(CAT_TOWNSFOLK, WAKE_NEVER, 0, false, false, true),
    /* CHAR_SnakeCharmer */   make_meta(CAT_TOWNSFOLK, WAKE_EACH_NIGHT),
    /* CHAR_Soldier */        make_meta(CAT_TOWNSFOLK, WAKE_NEVER),
    /* CHAR_Spy */            make_meta(CAT_MINION, WAKE_EACH_NIGHT, CAT_TOWNSFOLK | CAT_OUTSIDER),
    /* CHAR_Steward */        make_meta(CAT_TOWNSFOLK, WAKE_FIRST_NIGHT),
    /* CHAR_Sweetheart */     make_meta(CAT_OUTSIDER, WAKE_NEVER),
    /* CHAR_TeaLady */        make_meta(CAT_TOWNSFOLK, WAKE_NEVER, 0, false, false, false, (1 << CB_POST_DEATH) | (1 << CB_ALIGNMENT_CHANGE)),
    /* CHAR_TownCrier */      make_meta(CAT_TOWNSFOLK, WAKE_EACH_NIGHT_STAR),
    /* CHAR_Undertaker */     make_meta(CAT_TOWNSFOLK, WAKE_EACH_NIGHT_STAR),
    /* CHAR_Vigormortis */    make_meta(CAT_DEMON, WAKE_EACH_NIGHT_STAR),
    /* CHAR_VillageIdiot */   make_meta(CAT_TOWNSFOLK, WAKE_EACH_NIGHT),
    /* CHAR_Virgin */         make_meta(CAT_TOWNSFOLK, WAKE_NEVER, 0, false, false, true),
    /* CHAR_Vortox */         make_meta(CAT_DEMON, WAKE_EACH_NIGHT_STAR),
    /* CHAR_Washerwoman */    make_meta(CAT_TOWNSFOLK, WAKE_FIRST_NIGHT),
    /* CHAR_Widow */          make_meta(CAT_MINION, WAKE_FIRST_NIGHT),
    /* CHAR_Witch */          make_meta(CAT_MINION, WAKE_EACH_NIGHT),
    /* CHAR_Xaan */           make_meta(CAT_MINION, WAKE_NEVER),
    /* CHAR_Zombuul */        make_meta(CAT_DEMON, WAKE_MANUAL),
};

// Lightweight zero-allocation continuation callback (replaces Python yield / yield from)
struct YieldFn {
    void (*fn)(State&, void*);
    void* ctx;
    inline void operator()(State& s) const {
        if (!s.cull_branch) {
            fn(s, ctx);
        }
    }
};

template <typename F>
inline YieldFn make_yield(F& lambda) {
    return YieldFn{
        [](State& s, void* ctx) { (*static_cast<F*>(ctx))(s); },
        static_cast<void*>(&lambda)
    };
}

// Helper for chaining a generator across a sequence [0..count-1] (replaces core.apply_all loop)
template <typename StepFn>
void apply_seq(State& state, int idx, int count, StepFn& step_fn, YieldFn yield) {
    if (idx >= count) {
        yield(state);
        return;
    }
    auto next = [&](State& substate) {
        apply_seq(substate, idx + 1, count, step_fn, yield);
    };
    step_fn(state, idx, make_yield(next));
}

inline AbilityInstance make_ability(CharacterID type, uint8_t first_night = 1) {
    AbilityInstance ab{};
    ab.type = type;
    ab.first_night = first_night;
    ab.ability_src = NONE_PLAYER;
    ab.effects_active = false;
    ab.spent = false;
    ab.has_spent_attr = CHAR_META[type].has_spent;
    ab.vigormortised = false;
    ab.self_droison = (type == CHAR_Drunk);
    ab.target = NONE_PLAYER;
    ab.aux_target = NONE_PLAYER;
    ab.prev_category = 0;
    ab.prev_regs_mask = 0;
    ab.choice_night = -1;
    ab.aux_bool = false;
    return ab;
}

inline Category get_category(CharacterID type) {
    return CHAR_META[type].category;
}

inline bool is_category(CharacterID type, uint8_t cat_mask) {
    return (CHAR_META[type].category & cat_mask) != 0;
}

inline AbilityInstance* get_ability(Player& p, CharacterID type) {
    if (type == CHAR_NONE || p.character.type == type) {
        return &p.character;
    }
    return nullptr;
}

inline const AbilityInstance* get_ability(const Player& p, CharacterID type) {
    if (type == CHAR_NONE || p.character.type == type) {
        return &p.character;
    }
    return nullptr;
}

inline bool has_ability(const Player& p, CharacterID type) {
    return get_ability(p, type) != nullptr;
}

inline bool ability_acts_like(const Player& p, CharacterID type) {
    if (p.character.type == type) return true;
    if (p.has_drunklike_char && p.drunklike_char.type == type) return true;
    return false;
}

inline AbilityInstance* get_ability_that_acts_like(Player& p, CharacterID type) {
    if (p.character.type == type) return &p.character;
    if (p.has_drunklike_char && p.drunklike_char.type == type) return &p.character;
    return nullptr;
}

inline bool is_droisoned(const State& state, const AbilityInstance& ab, PlayerID me) {
    PlayerID pid = (ab.ability_src != NONE_PLAYER) ? ab.ability_src : me;
    return state.players[pid].droison_count > 0;
}

inline uint8_t get_misreg_categories(const State& state, const Player& p, bool assume_droisoned = false) {
    if (p.droison_count > 0 || assume_droisoned) {
        return 0;
    }
    return CHAR_META[p.character.type].misregister_categories;
}

inline bool behaves_evil(const State& state, PlayerID pid) {
    if (pid == 0 && state.puzzle->player_zero_is_you) {
        return false;
    }
    const Player& p = state.players[pid];
    if (p.speculative_good) return false;
    if (p.is_evil || p.speculative_evil) return true;
    if (ability_acts_like(p, CHAR_Lunatic) || ability_acts_like(p, CHAR_Politician)) {
        return true;
    }
    return false;
}

inline bool draws_wrong_token(CharacterID type) {
    return CHAR_META[type].is_drunklike;
}

inline bool lies_about_character(const State& state, PlayerID pid, bool ignore_own_ability = false) {
    const Player& p = state.players[pid];
    if (pid == 0 && state.puzzle->player_zero_is_you) {
        return draws_wrong_token(p.character.type);
    }
    return behaves_evil(state, pid)
        || (CHAR_META[p.character.type].lies_about_character_and_info && !ignore_own_ability)
        || p.speculative_ceremad;
}

inline bool lies_about_info(const State& state, PlayerID pid) {
    const Player& p = state.players[pid];
    if (pid == 0 && state.puzzle->player_zero_is_you) {
        return draws_wrong_token(p.character.type);
    }
    return behaves_evil(state, pid)
        || CHAR_META[p.character.type].lies_about_character_and_info
        || (p.speculative_ceremad && p.character.type != p.claim);
}

inline int16_t get_night_info(const State& state, CharacterID char_id, PlayerID pid, int8_t night) {
    if (night <= 0 || night >= MAX_NIGHTS) return -1;
    return state.puzzle->night_info[pid][night][char_id];
}

inline int16_t get_day_info(const State& state, CharacterID char_id, PlayerID pid) {
    if (state.day <= 0 || state.day >= MAX_NIGHTS) return -1;
    return state.puzzle->day_info[pid][state.day][char_id];
}

inline void change_claim_if_claimed_change_tonight(State& state, PlayerID pid) {
    int16_t node_idx = get_night_info(state, CHAR_NONE, pid, state.night);
    if (node_idx != -1) {
        const InfoNode& node = state.puzzle->info_nodes[node_idx];
        if (node.type == NOTINFO_CHARACTER_CHANGE) {
            state.players[pid].claim = node.character1;
        }
    }
}

inline void math_misregistration(State& state, PlayerID pid, const STBool* result = nullptr) {
    uint16_t mask = static_cast<uint16_t>(1u << pid);
    if ((result != nullptr && result->exact_eq(STBoolVal::TRUE)) || (state.math_misregisterers_mask & mask)) {
        return;
    }
    state.math_misreg_bounds[1] += 1;
    state.math_misregisterers_mask |= mask;
    if (result == nullptr || !result->is_maybe()) {
        state.math_misreg_bounds[0] += 1;
    }
}

inline void exclude_player_from_math_tonight(State& state, PlayerID pid) {
    state.math_misregisterers_mask |= static_cast<uint16_t>(1u << pid);
}

inline void math_misregistration_tomorrow(State& state, PlayerID pid) {
    state.tomorrow_math_misreg_mask |= static_cast<uint16_t>(1u << pid);
}

inline int circle_distance(PlayerID a, PlayerID b, int n_players) {
    if (b < a) {
        return std::min<int>(a - b, n_players + b - a);
    }
    return std::min<int>(b - a, n_players + a - b);
}

// Forward declarations for character effects and callbacks
void maybe_activate_effects(State& state, AbilityInstance& ab, PlayerID me, Reason reason = REASON_NONE);
void maybe_deactivate_effects(State& state, AbilityInstance& ab, PlayerID me, Reason reason = REASON_NONE);
void update_character_callbacks(State& state);
STBool eval_info(State& state, int16_t node_idx, PlayerID src);

inline void droison_player(State& state, PlayerID target, PlayerID src) {
    Player& p = state.players[target];
    p.droison_count += 1;
    maybe_deactivate_effects(state, p.character, target, REASON_DROISON);
}

inline void undroison_player(State& state, PlayerID target, PlayerID src) {
    Player& p = state.players[target];
    p.droison_count -= 1;
    maybe_activate_effects(state, p.character, target, REASON_DROISON);
}

// Core Info evaluation helpers
inline STBool eval_is_evil(const State& state, PlayerID target, PlayerID src = NONE_PLAYER) {
    const Player& p = state.players[target];
    if (p.character.type == CHAR_Recluse && !is_droisoned(state, p.character, target)) {
        return p.is_evil ? STBoolVal::TRUE : STBoolVal::FALSE_MAYBE;
    }
    if (p.character.type == CHAR_Spy && !is_droisoned(state, p.character, target)) {
        return p.is_evil ? STBoolVal::TRUE_MAYBE : STBoolVal::FALSE;
    }
    return STBool(p.is_evil);
}

inline STBool eval_is_alive(const State& state, PlayerID target, PlayerID src = NONE_PLAYER) {
    const Player& p = state.players[target];
    if (p.is_dead) return STBoolVal::FALSE;
    if (p.character.type == CHAR_Zombuul && p.character.aux_bool) {
        return STBoolVal::FALSE_LYING;
    }
    return STBoolVal::TRUE;
}

inline STBool eval_is_character(const State& state, PlayerID target, CharacterID char_id, PlayerID src = NONE_PLAYER) {
    const Player& p = state.players[target];
    uint8_t misreg = get_misreg_categories(state, p, false);
    bool truth = (p.character.type == char_id);
    bool is_maybe = ((CHAR_META[char_id].category & misreg) != 0) || (truth && misreg != 0);
    return STBool(truth, is_maybe, truth);
}

inline STBool eval_is_category(
    const State& state,
    PlayerID target,
    uint8_t cat_mask,
    bool assume_droisoned = false,
    PlayerID src = NONE_PLAYER
) {
    const Player& p = state.players[target];
    uint8_t misreg = get_misreg_categories(state, p, assume_droisoned);
    bool truth = is_category(p.character.type, cat_mask);
    bool is_maybe = ((cat_mask & misreg) != 0) || (truth && misreg != 0);
    return STBool(truth, is_maybe, truth);
}

inline STBool eval_is_in_play(const State& state, CharacterID char_id, PlayerID src = NONE_PLAYER) {
    STBool result = STBoolVal::FALSE;
    int N = state.puzzle->num_players;
    for (PlayerID pid = 0; pid < N; ++pid) {
        result |= eval_is_character(state, pid, char_id, src);
        if (result.exact_eq(STBoolVal::TRUE)) {
            return STBoolVal::TRUE;
        }
    }
    return result;
}

inline STBool eval_exactly_n(int N_target, const STBool* results, int count) {
    int truth_sum = 0;
    int st_says_sum = 0;
    int num_looks_true = 0;
    int num_maybes = 0;
    for (int i = 0; i < count; ++i) {
        truth_sum += results[i].truth() ? 1 : 0;
        st_says_sum += results[i].st_says() ? 1 : 0;
        num_looks_true += results[i].is_true() ? 1 : 0;
        num_maybes += results[i].is_maybe() ? 1 : 0;
    }
    bool truth = (N_target == truth_sum);
    bool st_says = (N_target == st_says_sum);
    bool is_maybe = num_maybes ? (num_looks_true <= N_target && N_target <= num_looks_true + num_maybes) : false;
    return STBool(truth, is_maybe, st_says);
}

template <typename CondFn>
inline PlayerID get_next_player_who_is(const State& state, CondFn cond, PlayerID you, bool clockwise) {
    int step = clockwise ? 1 : -1;
    int n_players = state.puzzle->num_players;
    for (int i = 1; i <= n_players; ++i) {
        PlayerID player = static_cast<PlayerID>((you + step * i + n_players * 2) % n_players);
        if (cond(state, player)) {
            return player;
        }
    }
    return NONE_PLAYER;
}

inline int tf_to_droison_in_direction(const State& state, PlayerID src, int direction, PlayerID* out_candidates) {
    int N = state.puzzle->num_players;
    int count = 0;
    for (int step = 1; step < N; ++step) {
        PlayerID player = static_cast<PlayerID>((src + direction * step + N * 2) % N);
        STBool is_tf = eval_is_category(state, player, CAT_TOWNSFOLK, true, src);
        if (is_tf.not_false()) {
            out_candidates[count++] = player;
        }
        if (is_tf.is_true()) {
            break;
        }
    }
    return count;
}

inline STBool cant_die(const State& state, PlayerID pid) {
    if (state.pithag_preventing_kills != NONE_PLAYER) {
        return STBoolVal::TRUE;
    }
    STBool result = STBoolVal::FALSE;
    const Player& p = state.players[pid];
    for (int i = 0; i < state.puzzle->num_players; ++i) {
        if (p.protection_map[i] & 0x80) {
            result |= STBool(static_cast<uint8_t>(p.protection_map[i] & 0x07));
        }
    }
    return result;
}

inline STBool safe_from_attacker(const State& state, PlayerID pid, PlayerID attacker) {
    STBool cd = cant_die(state, pid);
    STBool is_demon = eval_is_category(state, attacker, CAT_DEMON, false, pid);
    const Player& p = state.players[pid];
    STBool safe_from_demon = STBool(p.safe_from_demon_count > 0 || state.active_princesses > 0);
    return cd | (is_demon & safe_from_demon);
}

inline bool wakes_tonight_ability(const State& state, const AbilityInstance& ab, PlayerID me) {
    const Player& player = state.players[me];
    if (CHAR_META[ab.type].is_drunklike) {
        if (!player.has_drunklike_char) return false;
        return wakes_tonight_ability(state, player.drunklike_char, me);
    }
    if (ab.type == CHAR_Juggler) {
        return !player.is_dead
            && state.night == ab.first_night + 1
            && get_night_info(state, CHAR_Juggler, me, state.night) != -1;
    }
    if (ab.type == CHAR_Ravenkeeper || ab.type == CHAR_Sage) {
        return get_night_info(state, ab.type, me, state.night) != -1;
    }
    if (ab.type == CHAR_ScarletWoman) {
        return false;
    }
    if (player.is_dead || (is_category(ab.type, CAT_DEMON) && player.exorcised_count > 0)) {
        return false;
    }
    switch (CHAR_META[ab.type].wake_pattern) {
        case WAKE_NEVER:
            return false;
        case WAKE_FIRST_NIGHT:
            return state.night == ab.first_night;
        case WAKE_EACH_NIGHT:
            return true;
        case WAKE_EACH_NIGHT_STAR:
            return state.night != ab.first_night;
        case WAKE_EACH_NIGHT_UNTIL_SPENT:
            return !ab.spent;
        case WAKE_MANUAL:
            return false;
    }
    return false;
}

inline bool player_upcoming_in_night_order(const State& state, PlayerID pid) {
    for (int i = 0; i < state.num_players_still_to_act; ++i) {
        if (state.players_still_to_act[i] == pid) return true;
    }
    CharacterID char_t = state.players[pid].character.type;
    for (int idx = state.phase_order_index + 1; idx < state.puzzle->num_night_order; ++idx) {
        if (state.puzzle->night_order[idx] == char_t) return true;
    }
    return false;
}

STBool eval_info(State& state, int16_t node_idx, PlayerID src) {
    const InfoNode& node = state.puzzle->info_nodes[node_idx];
    const int N = state.puzzle->num_players;

    switch (node.type) {
        case INFO_OP_OR:
            return eval_info(state, node.child_a, src) | eval_info(state, node.child_b, src);
        case INFO_OP_AND:
            return eval_info(state, node.child_a, src) & eval_info(state, node.child_b, src);
        case INFO_OP_XOR:
            return eval_info(state, node.child_a, src) ^ eval_info(state, node.child_b, src);
        case INFO_OP_EQ:
            return eval_info(state, node.child_a, src) == eval_info(state, node.child_b, src);
        case INFO_OP_INVERT:
            return ~eval_info(state, node.child_a, src);

        case INFO_IS_EVIL:
            return eval_is_evil(state, node.player1, src);
        case INFO_IS_DROISONED:
            return STBool(state.players[node.player1].droison_count > 0);
        case INFO_IS_ALIVE:
            return eval_is_alive(state, node.player1, src);
        case INFO_IS_CHARACTER:
            return eval_is_character(state, node.player1, node.character1, src);
        case INFO_IS_CATEGORY:
            return eval_is_category(state, node.player1, node.category, node.flag != 0, src);
        case INFO_CHAR_ATTR_EQ: {
            const AbilityInstance& ch = state.players[node.player1].character;
            switch (static_cast<AttrID>(node.category)) {
                case ATTR_RED_HERRING:
                    return STBool(ch.type == CHAR_FortuneTeller && ch.target == node.player2);
                case ATTR_SELF_DROISON: {
                    bool has_attr = (ch.type == CHAR_Drunk || ch.type == CHAR_Lunatic
                        || ch.type == CHAR_Marionette || ch.type == CHAR_VillageIdiot
                        || ch.type == CHAR_SnakeCharmer || ch.type == CHAR_Philosopher);
                    return STBool(has_attr && ch.self_droison == (node.flag != 0));
                }
                case ATTR_TARGET:
                    return STBool(ch.target == node.player2);
                case ATTR_PUZZLE_DRUNK:
                    return STBool(ch.type == CHAR_Puzzlemaster && ch.target == node.player2);
                case ATTR_SPENT:
                    return STBool(ch.has_spent_attr && ch.spent == (node.flag != 0));
                default:
                    return STBoolVal::FALSE;
            }
        }
        case INFO_PLAYER_ATTR_EQ:
            return STBoolVal::FALSE;
        case INFO_IS_IN_PLAY:
            return eval_is_in_play(state, node.character1, src);
        case INFO_EXACTLY_N: {
            STBool sub[MAX_PLAYERS];
            for (int i = 0; i < node.extra_count; ++i) {
                sub[i] = eval_info(state, node.extra_indices[i], src);
            }
            return eval_exactly_n(node.count, sub, node.extra_count);
        }

        case INFO_DRUNK_BETWEEN_TOWNSFOLK: {
            STBool result = STBoolVal::FALSE;
            for (PlayerID p = 0; p < N; ++p) {
                STBool found_drunk = eval_is_character(state, p, CHAR_Drunk, src);
                if (found_drunk.is_false()) continue;
                PlayerID left = static_cast<PlayerID>((p - 1 + N) % N);
                PlayerID right = static_cast<PlayerID>((p + 1) % N);
                STBool tf_neighbours = eval_is_category(state, left, CAT_TOWNSFOLK, false, src)
                                     & eval_is_category(state, right, CAT_TOWNSFOLK, false, src);
                result |= (found_drunk & tf_neighbours);
            }
            return result;
        }

        case INFO_LONGEST_ROW_OF_TOWNSFOLK: {
            STBool townsfolk[MAX_PLAYERS];
            for (PlayerID p = 0; p < N; ++p) {
                townsfolk[p] = eval_is_category(state, p, CAT_TOWNSFOLK, false, src);
            }
            int longest = 0;
            int prev_not_tf = -1;
            for (int i = 0; i < 2 * N; ++i) {
                if (townsfolk[i % N].is_false()) {
                    longest = std::max(longest, i - prev_not_tf - 1);
                    prev_not_tf = i;
                }
            }
            if (prev_not_tf == -1) {
                longest = N;
            } else {
                longest = std::min(longest, N);
            }
            if (node.flag != 0) {
                return STBool(longest == node.count);
            } else {
                return STBool(node.min_val <= longest && longest <= node.max_val);
            }
        }

        case PING_ARTIST:
            return eval_info(state, node.child_a, src);

        case PING_SAVANT: {
            STBool a = eval_info(state, node.child_a, src);
            STBool b = eval_info(state, node.child_b, src);
            if (state.vortox) return a | b;
            return a ^ b;
        }

        case PING_CHEF: {
            STBool evils[MAX_PLAYERS + 1];
            for (int i = 0; i <= N; ++i) {
                evils[i] = eval_is_evil(state, static_cast<PlayerID>(i % N), src);
            }
            STBool pairs[MAX_PLAYERS];
            for (int i = 0; i < N; ++i) {
                pairs[i] = evils[i] & evils[i + 1];
            }
            return eval_exactly_n(node.count, pairs, N);
        }

        case PING_CLOCKMAKER: {
            struct Cand { PlayerID pid; STBool reg; };
            Cand minions[MAX_PLAYERS];
            Cand demons[MAX_PLAYERS];
            int n_minions = 0, n_demons = 0;
            for (PlayerID i = 0; i < N; ++i) {
                STBool m = eval_is_category(state, i, CAT_MINION, false, src);
                if (m.not_false()) minions[n_minions++] = {i, m};
                STBool d = eval_is_category(state, i, CAT_DEMON, false, src);
                if (d.not_false()) demons[n_demons++] = {i, d};
            }
            bool ignore_dead_demons = false;
            for (int i = 0; i < n_demons; ++i) {
                if (eval_is_alive(state, demons[i].pid, src).is_true()) {
                    ignore_dead_demons = true;
                    break;
                }
            }
            STBool correct_distance = STBoolVal::FALSE;
            STBool too_close = STBoolVal::FALSE;
            for (int di = 0; di < n_demons; ++di) {
                PlayerID demon_pos = demons[di].pid;
                if (state.players[demon_pos].is_dead && ignore_dead_demons) continue;
                for (int mi = 0; mi < n_minions; ++mi) {
                    PlayerID minion_pos = minions[mi].pid;
                    STBool is_pair = demons[di].reg & minions[mi].reg;
                    int dist = circle_distance(minion_pos, demon_pos, N);
                    if (dist < node.count) {
                        too_close |= is_pair;
                    } else if (dist == node.count) {
                        correct_distance |= is_pair;
                    }
                }
            }
            return correct_distance & ~too_close;
        }

        case PING_CHAMBERMAID: {
            bool valid_choices = (node.player1 != src && node.player2 != src)
                && eval_is_alive(state, node.player1, src).not_false()
                && eval_is_alive(state, node.player2, src).not_false();
            int wake_count = 0;
            PlayerID p_ids[2] = {node.player1, node.player2};
            for (PlayerID pid : p_ids) {
                const Player& p = state.players[pid];
                if (p.woke_tonight || (
                    player_upcoming_in_night_order(state, pid) &&
                    wakes_tonight_ability(state, p.character, pid)
                )) {
                    wake_count += 1;
                }
            }
            return STBool(valid_choices && wake_count == node.count);
        }

        case PING_DREAMER:
            return eval_is_character(state, node.player1, node.character1, src)
                 | eval_is_character(state, node.player1, node.character2, src);

        case PING_EMPATH: {
            auto cond = [&](const State& s, PlayerID p) {
                return eval_is_alive(s, p, src).is_true();
            };
            PlayerID left = get_next_player_who_is(state, cond, src, true);
            PlayerID right = get_next_player_who_is(state, cond, src, false);
            STBool neighbours[2];
            int n_nb = 1;
            neighbours[0] = eval_is_evil(state, left, src);
            if (left != right) {
                neighbours[1] = eval_is_evil(state, right, src);
                n_nb = 2;
            }
            return eval_exactly_n(node.count, neighbours, n_nb);
        }

        case PING_FORTUNE_TELLER: {
            const AbilityInstance* ft = get_ability(state.players[src], CHAR_FortuneTeller);
            STBool real_result = eval_is_category(state, node.player1, CAT_DEMON, false, src)
                               | eval_is_category(state, node.player2, CAT_DEMON, false, src);
            if (ft != nullptr && (ft->target == node.player1 || ft->target == node.player2)) {
                real_result |= STBoolVal::TRUE_LYING;
                if (real_result.exact_eq(STBoolVal::TRUE_LYING)) {
                    exclude_player_from_math_tonight(state, src);
                }
            }
            return real_result == STBool(node.flag != 0);
        }

        case PING_INVESTIGATOR:
        case PING_WASHERWOMAN:
            return eval_is_character(state, node.player1, node.character1, src)
                 | eval_is_character(state, node.player2, node.character1, src);

        case PING_JUGGLER: {
            Player& juggler_player = state.players[src];
            juggler_player.woke_tonight = true;
            return eval_exactly_n(node.count, juggler_player.correct_juggles, juggler_player.num_juggles);
        }

        case PING_KNIGHT:
            return ~(eval_is_category(state, node.player1, CAT_DEMON, false, src)
                   | eval_is_category(state, node.player2, CAT_DEMON, false, src));

        case PING_LIBRARIAN: {
            if (node.player1 == NONE_PLAYER) {
                STBool outs[MAX_PLAYERS];
                for (PlayerID i = 0; i < N; ++i) {
                    outs[i] = eval_is_category(state, i, CAT_OUTSIDER, false, src);
                }
                return eval_exactly_n(0, outs, N);
            }
            return eval_is_character(state, node.player1, node.character1, src)
                 | eval_is_character(state, node.player2, node.character1, src);
        }

        case PING_MATHEMATICIAN:
            return STBool(state.math_misreg_bounds[0] <= node.count && node.count <= state.math_misreg_bounds[1]);

        case PING_NOBLE: {
            STBool args[3] = {
                eval_is_evil(state, node.player1, src),
                eval_is_evil(state, node.player2, src),
                eval_is_evil(state, node.player3, src),
            };
            return eval_exactly_n(1, args, 3);
        }

        case PING_ORACLE: {
            STBool dead_evils[MAX_PLAYERS];
            for (PlayerID i = 0; i < N; ++i) {
                dead_evils[i] = eval_is_evil(state, i, src) & ~eval_is_alive(state, i, src);
            }
            return eval_exactly_n(node.count, dead_evils, N);
        }

        case PING_SEAMSTRESS: {
            STBool a = eval_is_evil(state, node.player1, src);
            STBool b = eval_is_evil(state, node.player2, src);
            STBool enemies = a ^ b;
            return (node.flag != 0) ? ~enemies : enemies;
        }

        case PING_STEWARD:
            return ~eval_is_evil(state, node.player1, src);

        case PING_UNDERTAKER: {
            int yesterday = state.night - 1;
            int ev_count = (yesterday > 0 && yesterday < MAX_NIGHTS) ? state.puzzle->day_event_counts[yesterday] : 0;
            const EventNode* evs = state.puzzle->day_events[yesterday];
            if (node.player1 == NONE_PLAYER) {
                bool any_exec_died = false;
                for (int i = 0; i < ev_count; ++i) {
                    if ((evs[i].type == EVENT_EXECUTION || evs[i].type == EVENT_EXECUTION_BY_ST) && evs[i].flag) {
                        any_exec_died = true;
                        break;
                    }
                }
                return STBool(!any_exec_died);
            } else {
                for (int i = 0; i < ev_count; ++i) {
                    if ((evs[i].type == EVENT_EXECUTION || evs[i].type == EVENT_EXECUTION_BY_ST)
                        && evs[i].player == node.player1 && evs[i].flag) {
                        return eval_is_character(state, node.player1, node.character1, src);
                    }
                }
                return STBoolVal::FALSE;
            }
        }

        case PING_VILLAGE_IDIOT:
            return eval_is_evil(state, node.player1, src) == STBool(node.flag != 0);

        case PING_SHUGENJA: {
            int direction = (node.flag != 0) ? 1 : -1;
            STBool evils[MAX_PLAYERS];
            for (int step = 1; step < N; ++step) {
                PlayerID pid = static_cast<PlayerID>((src + direction * step + N * 2) % N);
                evils[step] = eval_is_evil(state, pid, src);
            }
            int fwd_true = N, fwd_maybe = N, fwd_says = N;
            int bkwd_true = N, bkwd_maybe = N, bkwd_says = N;
            for (int step = N / 2; step >= 1; --step) {
                const STBool& f = evils[step];
                const STBool& b = evils[N - step];
                if (f.truth()) {
                    fwd_true = step;
                    fwd_maybe = step;
                } else if (f.is_maybe()) {
                    fwd_maybe = step;
                }
                if (f.st_says()) {
                    fwd_says = step;
                }
                if (b.truth()) {
                    bkwd_true = step;
                    bkwd_maybe = step;
                } else if (b.is_maybe()) {
                    bkwd_maybe = step;
                }
                if (b.st_says()) {
                    bkwd_says = step;
                }
            }
            bool truth = fwd_true <= bkwd_true;
            bool is_maybe = truth ? (bkwd_maybe <= fwd_true) : (fwd_maybe <= bkwd_true);
            bool st_says = fwd_says <= bkwd_says;
            return STBool(truth, is_maybe, st_says);
        }

        case PING_RAVENKEEPER: {
            const AbilityInstance* rk = get_ability(state.players[src], CHAR_Ravenkeeper);
            if (rk == nullptr || rk->choice_night != state.night) {
                return STBoolVal::FALSE;
            }
            STBool result = eval_is_character(state, node.player1, node.character1, src);
            if (rk->aux_bool) {
                math_misregistration(state, src, &result);
                return result ^ STBoolVal::FALSE_MAYBE;
            }
            return result;
        }

        case PING_SAGE: {
            const AbilityInstance* sage = get_ability(state.players[src], CHAR_Sage);
            if (sage == nullptr || sage->choice_night != state.night) {
                return STBoolVal::FALSE;
            }
            STBool result = eval_is_category(state, node.player1, CAT_DEMON, false, src)
                          | eval_is_category(state, node.player2, CAT_DEMON, false, src);
            if (sage->aux_bool) {
                math_misregistration(state, src, &result);
                return result ^ STBoolVal::FALSE_MAYBE;
            }
            return result;
        }

        case PING_PUZZLEMASTER: {
            STBool correct_demon = eval_is_category(state, node.player2, CAT_DEMON, false, src);
            const AbilityInstance* pm = get_ability(state.players[src], CHAR_Puzzlemaster);
            if (pm != nullptr && node.player1 == pm->target) {
                return correct_demon;
            }
            return ~correct_demon;
        }

        default:
            return STBoolVal::FALSE;
    }
}

bool default_info_check(
    State& state,
    AbilityInstance& ab,
    PlayerID me,
    bool even_if_dead = false,
    bool even_if_droisoned = false
) {
    int16_t ping_idx = -1;
    if (state.current_phase == PHASE_NIGHT) {
        ping_idx = get_night_info(state, ab.type, me, state.night);
    } else if (state.current_phase == PHASE_DAY) {
        ping_idx = get_day_info(state, ab.type, me);
    }

    Player& player = state.players[me];
    if (ping_idx == -1 || lies_about_info(state, me)) {
        return true;
    }
    if (player.is_dead && !even_if_dead) {
        return false;
    }
    if (ab.has_spent_attr) {
        if (ab.spent) {
            return false;
        }
        ab.spent = true;
    }

    STBool result = eval_info(state, ping_idx, me);
    if (result.st_lying()) {
        math_misregistration(state, me);
    }
    if (state.vortox && is_category(ab.type, CAT_TOWNSFOLK)) {
        math_misregistration(state, me);
        return !result.truth();
    }
    if (!even_if_droisoned && is_droisoned(state, ab, me)) {
        if (!ab.self_droison) {
            math_misregistration(state, me, &result);
        }
        return true;
    }
    return result.not_false();
}

// Effect activation & deactivation
void activate_effects_impl(State& state, AbilityInstance& ab, PlayerID me) {
    switch (ab.type) {
        case CHAR_Poisoner:
        case CHAR_Courtier:
            if (ab.target == me) {
                state.players[me].droison_count += 1;
            } else if (ab.target != NONE_PLAYER) {
                droison_player(state, ab.target, me);
            }
            break;
        case CHAR_Monk:
            if (ab.target != NONE_PLAYER) {
                state.players[ab.target].safe_from_demon_count += 1;
            }
            break;
        case CHAR_Soldier:
            state.players[me].safe_from_demon_count += 1;
            break;
        case CHAR_Vortox:
            state.vortox = true;
            break;
        case CHAR_TeaLady: {
            auto cond = [&](const State& s, PlayerID p) {
                return eval_is_alive(s, p, me).is_true();
            };
            PlayerID left = get_next_player_who_is(state, cond, me, true);
            PlayerID right = get_next_player_who_is(state, cond, me, false);
            STBool prot = ~eval_is_evil(state, left, me) & ~eval_is_evil(state, right, me);
            ab.target = left;
            ab.aux_target = right;
            state.players[left].protection_map[me] = 0x80 | prot.bits;
            state.players[right].protection_map[me] = 0x80 | prot.bits;
            break;
        }
        case CHAR_NoDashii:
            if (ab.target != NONE_PLAYER) droison_player(state, ab.target, me);
            if (ab.aux_target != NONE_PLAYER) droison_player(state, ab.aux_target, me);
            break;
        case CHAR_Pukka:
            if (ab.target != NONE_PLAYER) droison_player(state, ab.target, me);
            break;
        case CHAR_SnakeCharmer:
            if (ab.self_droison) state.players[me].droison_count += 1;
            break;
        case CHAR_Witch:
            if (ab.target != NONE_PLAYER) {
                state.players[ab.target].witch_cursed = me;
            }
            break;
        case CHAR_Princess:
            if (ab.aux_bool) {
                state.active_princesses += 1;
            }
            break;
        case CHAR_Xaan:
            if (ab.aux_bool) {
                for (PlayerID pid = 0; pid < state.puzzle->num_players; ++pid) {
                    if (ab.aux_mask & (1u << pid)) {
                        droison_player(state, pid, me);
                    }
                }
            }
            break;
        default:
            break;
    }
}

void deactivate_effects_impl(State& state, AbilityInstance& ab, PlayerID me) {
    switch (ab.type) {
        case CHAR_Poisoner:
        case CHAR_Courtier:
            if (ab.target == me) {
                state.players[me].droison_count -= 1;
            } else if (ab.target != NONE_PLAYER) {
                undroison_player(state, ab.target, me);
            }
            break;
        case CHAR_Monk:
            if (ab.target != NONE_PLAYER) {
                state.players[ab.target].safe_from_demon_count -= 1;
            }
            break;
        case CHAR_Soldier:
            state.players[me].safe_from_demon_count -= 1;
            break;
        case CHAR_Vortox:
            state.vortox = false;
            break;
        case CHAR_TeaLady:
            if (ab.target != NONE_PLAYER) state.players[ab.target].protection_map[me] = 0;
            if (ab.aux_target != NONE_PLAYER) state.players[ab.aux_target].protection_map[me] = 0;
            break;
        case CHAR_NoDashii:
            if (ab.target != NONE_PLAYER) undroison_player(state, ab.target, me);
            if (ab.aux_target != NONE_PLAYER) undroison_player(state, ab.aux_target, me);
            break;
        case CHAR_Pukka:
            if (ab.target != NONE_PLAYER && ab.target != me) {
                undroison_player(state, ab.target, me);
            }
            break;
        case CHAR_SnakeCharmer:
            if (ab.self_droison) undroison_player(state, me, me);
            break;
        case CHAR_Witch:
            if (ab.target != NONE_PLAYER) {
                state.players[ab.target].witch_cursed = NONE_PLAYER;
            }
            break;
        case CHAR_Princess:
            if (ab.aux_bool) {
                state.active_princesses -= 1;
            }
            break;
        case CHAR_Xaan:
            if (ab.aux_bool) {
                for (PlayerID pid = 0; pid < state.puzzle->num_players; ++pid) {
                    if (ab.aux_mask & (1u << pid)) {
                        undroison_player(state, pid, me);
                    }
                }
            }
            break;
        default:
            break;
    }
}

void maybe_activate_effects(State& state, AbilityInstance& ab, PlayerID me, Reason reason) {
    if (ab.type == CHAR_Puzzlemaster) {
        if (!ab.effects_active && !is_droisoned(state, ab, me) && reason != REASON_RESURRECTION) {
            ab.effects_active = true;
            droison_player(state, ab.target, me);
        }
        return;
    }
    Player& player = state.players[me];
    if (!ab.effects_active && !is_droisoned(state, ab, me) && (!player.is_dead || ab.vigormortised)) {
        ab.effects_active = true;
        activate_effects_impl(state, ab, me);
    }
}

void maybe_deactivate_effects(State& state, AbilityInstance& ab, PlayerID me, Reason reason) {
    if (ab.type == CHAR_Puzzlemaster) {
        if (ab.effects_active && reason != REASON_DEATH && ab.target != me) {
            ab.effects_active = false;
            undroison_player(state, ab.target, me);
        }
        return;
    }
    if (reason == REASON_DEATH && ab.vigormortised) {
        return;
    }
    if (ab.effects_active) {
        ab.effects_active = false;
        deactivate_effects_impl(state, ab, me);
    }
}

void update_character_callbacks(State& state) {
    for (int cb = 0; cb < CB_COUNT; ++cb) {
        state.character_callbacks[cb] = 0;
    }
    int N = state.puzzle->num_players;
    for (PlayerID pid = 0; pid < N; ++pid) {
        uint8_t mask = CHAR_META[state.players[pid].character.type].callbacks_mask;
        for (int cb = 0; cb < CB_COUNT; ++cb) {
            if (mask & (1 << cb)) {
                state.character_callbacks[cb] |= static_cast<uint16_t>(1u << pid);
            }
        }
    }
}

bool check_game_over(const State& state) {
    int N = state.puzzle->num_players;
    bool all_demons_dead = true;
    bool no_evil_twin = true;
    for (PlayerID pid = 0; pid < N; ++pid) {
        const Player& p = state.players[pid];
        if (is_category(p.character.type, CAT_DEMON) && !p.is_dead) {
            all_demons_dead = false;
        }
        if (p.character.type == CHAR_EvilTwin && (!p.is_dead || p.character.vigormortised) && p.droison_count == 0) {
            no_evil_twin = false;
        }
    }
    return all_demons_dead && no_evil_twin;
}

// Forward declarations for character lifecycle methods
void run_character_setup(State& state, PlayerID me, YieldFn yield);
void run_character_night(State& state, PlayerID me, YieldFn yield);
void run_character_day(State& state, PlayerID me, YieldFn yield);
void run_character_end_night(State& state, PlayerID me, YieldFn yield);
void run_character_end_day(State& state, PlayerID me, YieldFn yield);
void trigger_callback(State& state, CallbackType cb, PlayerID arg, YieldFn yield);
void change_character(State& state, PlayerID pid, CharacterID new_char, YieldFn yield);
void apply_death(State& state, PlayerID me, PlayerID src, YieldFn yield);
void attacked_at_night(State& state, PlayerID me, PlayerID src, YieldFn yield);
void char_killed(State& state, PlayerID me, PlayerID src, YieldFn yield);
void char_executed(State& state, PlayerID me, bool died, YieldFn yield);

// ScarletWoman helper
struct SWCatchResult {
    STBool catches;
    STBool fumble_droison;
};

SWCatchResult scarlet_woman_catches_death(const State& state, PlayerID dying_id, PlayerID sw_id) {
    const Player& scarletwoman = state.players[sw_id];
    const AbilityInstance* sw_ability = get_ability(scarletwoman, CHAR_ScarletWoman);
    if (sw_ability == nullptr) {
        return {STBoolVal::FALSE, STBoolVal::FALSE};
    }
    int living_player_count = 0;
    for (PlayerID i = 0; i < state.puzzle->num_players; ++i) {
        if (!state.players[i].is_dead && !is_category(state.players[i].character.type, CAT_TRAVELLER)) {
            living_player_count += 1;
        }
    }
    STBool ability_active = STBool(living_player_count >= 5 && (!scarletwoman.is_dead || sw_ability->vigormortised));
    STBool demon_dying = eval_is_category(state, dying_id, CAT_DEMON, false, sw_id);
    STBool would_catch = demon_dying & ability_active;
    bool sw_droisoned = is_droisoned(state, *sw_ability, sw_id);
    if (would_catch.not_false() && sw_droisoned) {
        return {STBoolVal::FALSE, ~would_catch};
    }
    return {would_catch, STBoolVal::FALSE};
}

void run_callback_for_caller(State& state, CallbackType cb, PlayerID caller, PlayerID arg, YieldFn yield) {
    CharacterID ctype = state.players[caller].character.type;
    if (cb == CB_PRE_DEATH) {
        if (ctype == CHAR_ScarletWoman) {
            SWCatchResult res = scarlet_woman_catches_death(state, arg, caller);
            if (res.catches.not_false()) {
                if (res.catches.is_maybe()) {
                    State substate = state;
                    if (has_ability(state.players[arg], CHAR_ScarletWoman)) {
                        STBool inv_d = ~res.fumble_droison;
                        math_misregistration(substate, caller, &inv_d);
                    }
                    yield(substate);
                }
                const Player& dying_player = state.players[arg];
                CharacterID possible_demons[MAX_SCRIPT];
                int n_demons = 0;
                auto add_demon = [&](CharacterID d) {
                    if (d == CHAR_Recluse) return;
                    for (int i = 0; i < n_demons; ++i) {
                        if (possible_demons[i] == d) return;
                    }
                    possible_demons[n_demons++] = d;
                };
                if (is_category(dying_player.character.type, CAT_DEMON)) {
                    add_demon(dying_player.character.type);
                }
                if (has_ability(dying_player, CHAR_Recluse) && !is_droisoned(state, dying_player.character, arg)) {
                    for (int i = 0; i < state.puzzle->num_demons; ++i) {
                        add_demon(state.puzzle->demons[i]);
                    }
                }
                for (int i = 0; i < n_demons; ++i) {
                    State substate = state;
                    if (substate.night != 0) {
                        substate.players[caller].woke_tonight = true;
                    }
                    change_character(substate, caller, possible_demons[i], yield);
                }
            } else {
                yield(state);
            }
            return;
        } else if (ctype == CHAR_EvilTwin) {
            Player& et = state.players[caller];
            if ((et.is_dead && !et.character.vigormortised)
                || (arg != et.character.target && arg != caller)
                || eval_is_evil(state, arg, caller).not_false()) {
                yield(state);
            } else if (is_droisoned(state, et.character, caller)) {
                math_misregistration(state, caller);
                yield(state);
            }
            return;
        }
    } else if (cb == CB_POST_DEATH || cb == CB_ALIGNMENT_CHANGE) {
        if (ctype == CHAR_TeaLady) {
            AbilityInstance& ab = state.players[caller].character;
            maybe_deactivate_effects(state, ab, caller);
            maybe_activate_effects(state, ab, caller);
            yield(state);
            return;
        }
    } else if (cb == CB_CHARACTER_CHANGE) {
        if (ctype == CHAR_NoDashii) {
            PlayerID fwd_candidates[MAX_PLAYERS];
            PlayerID bkwd_candidates[MAX_PLAYERS];
            int n_fwd = tf_to_droison_in_direction(state, caller, 1, fwd_candidates);
            int n_bkwd = tf_to_droison_in_direction(state, caller, -1, bkwd_candidates);
            bool effects_active = state.players[caller].character.effects_active;
            for (int fi = 0; fi < n_fwd; ++fi) {
                for (int bi = 0; bi < n_bkwd; ++bi) {
                    PlayerID fwd = fwd_candidates[fi];
                    PlayerID bkwd = bkwd_candidates[bi];
                    State new_state = state;
                    AbilityInstance& nodashii = new_state.players[caller].character;
                    PlayerID old_fwd = nodashii.target;
                    PlayerID old_bkwd = nodashii.aux_target;
                    if (effects_active) {
                        if (fwd != old_fwd) {
                            undroison_player(new_state, old_fwd, caller);
                            droison_player(new_state, fwd, caller);
                        } else if (bkwd != old_bkwd) {
                            undroison_player(new_state, old_bkwd, caller);
                            droison_player(new_state, bkwd, caller);
                        }
                    }
                    nodashii.target = fwd;
                    nodashii.aux_target = bkwd;
                    yield(new_state);
                }
            }
            return;
        }
    }
    yield(state);
}

void trigger_callback(State& state, CallbackType cb, PlayerID arg, YieldFn yield) {
    uint16_t mask = state.character_callbacks[cb];
    if (mask == 0) {
        yield(state);
        return;
    }
    PlayerID callers[MAX_PLAYERS];
    int count = 0;
    for (PlayerID pid = 0; pid < state.puzzle->num_players; ++pid) {
        if (mask & (1u << pid)) {
            callers[count++] = pid;
        }
    }
    auto step = [&](State& s, int idx, YieldFn y) {
        run_callback_for_caller(s, cb, callers[idx], arg, y);
    };
    apply_seq(state, 0, count, step, yield);
}

void post_death_in_town(State& state, PlayerID dead_player, YieldFn yield) {
    auto after_cb = [&](State& s) {
        CharacterID dead_char = s.players[dead_player].character.type;
        if (!is_category(dead_char, CAT_DEMON) || !check_game_over(s)) {
            yield(s);
        }
    };
    trigger_callback(state, CB_POST_DEATH, dead_player, make_yield(after_cb));
}

void apply_death(State& state, PlayerID me, PlayerID src, YieldFn yield) {
    CharacterID ctype = state.players[me].character.type;
    if (ctype == CHAR_Ravenkeeper) {
        if (state.night != 0) {
            state.players[me].character.choice_night = state.night;
            state.players[me].character.aux_bool = is_droisoned(state, state.players[me].character, me);
            state.players[me].woke_tonight = true;
        }
    } else if (ctype == CHAR_Sage) {
        STBool killed_by_demon = (src != NONE_PLAYER)
            ? eval_is_category(state, src, CAT_DEMON, false, me)
            : STBoolVal::FALSE;
        if (state.night != 0 && killed_by_demon.not_false()) {
            state.players[me].character.choice_night = state.night;
            state.players[me].character.aux_bool = is_droisoned(state, state.players[me].character, me);
            state.players[me].woke_tonight = true;
        }
    }

    auto after_pre_death = [&](State& substate) {
        Player& player = substate.players[me];
        player.is_dead = true;
        maybe_deactivate_effects(substate, player.character, me, REASON_DEATH);
        if (ctype == CHAR_Mutant) {
            auto after_post = [&](State& s2) {
                change_claim_if_claimed_change_tonight(s2, me);
                if (s2.players[me].claim == CHAR_Mutant || lies_about_character(s2, me, true)) {
                    yield(s2);
                }
            };
            post_death_in_town(substate, me, make_yield(after_post));
        } else {
            post_death_in_town(substate, me, yield);
        }
    };
    trigger_callback(state, CB_PRE_DEATH, me, make_yield(after_pre_death));
}

void attacked_at_night(State& state, PlayerID me, PlayerID src, YieldFn yield) {
    Player& player = state.players[me];
    if (player.is_dead) {
        if (state.puzzle->allow_killing_dead_players) {
            yield(state);
        }
        return;
    }
    STBool safe = safe_from_attacker(state, me, src);
    if (safe.not_false()) {
        math_misregistration(state, src);
        if (safe.is_maybe()) {
            State forked = state;
            yield(forked);
        } else {
            yield(state);
        }
    }
    if (safe.not_true()) {
        apply_death(state, me, src, yield);
    }
}

void char_killed(State& state, PlayerID me, PlayerID src, YieldFn yield) {
    Player& player = state.players[me];
    if (cant_die(state, me).not_true() && !player.is_dead) {
        apply_death(state, me, src, yield);
    }
}

void default_executed(State& state, PlayerID me, bool died, YieldFn yield) {
    Player& player = state.players[me];
    if (player.is_dead) {
        yield(state);
    }
    STBool cd = cant_die(state, me);
    if (died && cd.not_true()) {
        char_killed(state, me, NONE_PLAYER, yield);
    } else if (!died && (cd.not_false() || player.safe_from_execution > 0)) {
        yield(state);
    }
}

void char_executed(State& state, PlayerID me, bool died, YieldFn yield) {
    Player& player = state.players[me];
    if (player.character.type == CHAR_Saint) {
        bool droisoned = is_droisoned(state, player.character, me);
        if (droisoned) {
            math_misregistration(state, me);
        }
        if (droisoned || !died) {
            default_executed(state, me, died, yield);
        }
        return;
    }
    default_executed(state, me, died, yield);
}

void change_character(State& state, PlayerID pid, CharacterID new_char, YieldFn yield) {
    Player& player = state.players[pid];
    maybe_deactivate_effects(state, player.character, pid, REASON_CHARACTER_CHANGE);

    // Remove pid from players_still_to_act if present
    for (int i = 0; i < state.num_players_still_to_act; ++i) {
        if (state.players_still_to_act[i] == pid) {
            for (int j = i; j + 1 < state.num_players_still_to_act; ++j) {
                state.players_still_to_act[j] = state.players_still_to_act[j + 1];
            }
            state.num_players_still_to_act -= 1;
            break;
        }
    }

    uint8_t next_night = (state.night != 0) ? state.night : static_cast<uint8_t>(state.day + 1);
    player.character = make_ability(new_char, next_night);
    player.has_drunklike_char = false;
    update_character_callbacks(state);
    change_claim_if_claimed_change_tonight(state, pid);

    auto after_setup = [&](State& substate) {
        if (!check_game_over(substate)) {
            bool be = behaves_evil(substate, pid);
            substate.players[pid].ever_behaved_evil |= be;
            trigger_callback(substate, CB_CHARACTER_CHANGE, pid, yield);
        }
    };
    run_character_setup(state, pid, make_yield(after_setup));
}

void change_alignment(State& state, PlayerID pid, bool is_evil, YieldFn yield) {
    Player& player = state.players[pid];
    if (player.is_evil == is_evil) {
        yield(state);
        return;
    }
    player.is_evil = is_evil;
    player.ever_behaved_evil |= behaves_evil(state, pid);
    trigger_callback(state, CB_ALIGNMENT_CHANGE, pid, yield);
}

// Drunklike simulation
bool drunklike_worth_simulating(const Player& p) {
    if (!p.has_drunklike_char) return false;
    WakePattern wp = CHAR_META[p.drunklike_char.type].wake_pattern;
    return wp == WAKE_MANUAL || wp == WAKE_EACH_NIGHT_UNTIL_SPENT;
}

void drunklike_extract_from_simulation(State& state, const State& sim_state, PlayerID me) {
    Player& real_player = state.players[me];
    const Player& sim_player = sim_state.players[me];
    if (sim_player.character.has_spent_attr) {
        real_player.character.spent = sim_player.character.spent;
    }
    real_player.woke_tonight |= sim_player.woke_tonight;
    real_player.drunklike_char = sim_player.character;
}

void drunklike_run_simulation(State& state, PlayerID me, YieldFn yield) {
    Player& player = state.players[me];
    if (!drunklike_worth_simulating(player)) {
        player.character.spent = false;
        yield(state);
        return;
    }

    State sim_state = state;
    Player& sim_player = sim_state.players[me];
    sim_player.character = sim_player.drunklike_char;
    sim_player.has_drunklike_char = false;

    bool any_substates = false;
    auto on_sim_substate = [&](State& sim_substate) {
        any_substates = true;
        State substate = state;
        drunklike_extract_from_simulation(substate, sim_substate, me);
        yield(substate);
    };

    if (state.current_phase == PHASE_SETUP) {
        run_character_setup(sim_state, me, make_yield(on_sim_substate));
    } else if (state.current_phase == PHASE_NIGHT) {
        run_character_night(sim_state, me, make_yield(on_sim_substate));
    }

    if (!any_substates) {
        drunklike_extract_from_simulation(state, sim_state, me);
        yield(state);
    }
}

bool resurrection_possible(const SerializedPuzzle& puzzle) {
    for (int i = 0; i < puzzle.num_script; ++i) {
        CharacterID c = puzzle.script[i];
        if (c == CHAR_Professor || c == CHAR_AlHadikhia || c == CHAR_Shabaloth) {
            return true;
        }
    }
    return false;
}

int generic_demon_get_targets(const State& state, PlayerID me, PlayerID* out_targets) {
    int N = state.puzzle->num_players;
    if (!resurrection_possible(*state.puzzle)) {
        uint16_t target_mask = 0;
        int nd_count = state.puzzle->night_death_counts[state.night];
        for (int i = 0; i < nd_count; ++i) {
            const NightDeathNode& nd = state.puzzle->night_deaths[state.night][i];
            if (!nd.is_resurrection && !state.players[nd.player].is_dead) {
                target_mask |= static_cast<uint16_t>(1u << nd.player);
            }
        }
        PlayerID dead_target = NONE_PLAYER;
        PlayerID safe_target = NONE_PLAYER;
        for (PlayerID pid = 0; pid < N; ++pid) {
            if (state.players[pid].is_dead) {
                dead_target = pid;
            } else if (safe_from_attacker(state, pid, me).not_false()) {
                safe_target = pid;
            }
        }
        if (dead_target != NONE_PLAYER) target_mask |= static_cast<uint16_t>(1u << dead_target);
        if (safe_target != NONE_PLAYER) target_mask |= static_cast<uint16_t>(1u << safe_target);

        int count = 0;
        for (PlayerID pid = 0; pid < N; ++pid) {
            if (target_mask & (1u << pid)) {
                out_targets[count++] = pid;
            }
        }
        return count;
    }

    int count = 0;
    bool sunk_a_kill = false;
    for (PlayerID pid = 0; pid < N; ++pid) {
        if (state.players[pid].is_dead) {
            if (sunk_a_kill) continue;
            sunk_a_kill = true;
        }
        out_targets[count++] = pid;
    }
    return count;
}

void run_character_setup(State& state, PlayerID me, YieldFn yield) {
    Player& player = state.players[me];
    AbilityInstance& ab = player.character;
    int N = state.puzzle->num_players;

    switch (ab.type) {
        case CHAR_Atheist:
            if (state.current_phase == PHASE_SETUP) {
                return;
            }
            yield(state);
            return;

        case CHAR_Drunk:
            if (!is_category(player.claim, CAT_TOWNSFOLK)) {
                return;
            }
            player.drunklike_char = make_ability(player.claim, ab.first_night);
            player.has_drunklike_char = true;
            drunklike_run_simulation(state, me, yield);
            return;

        case CHAR_Marionette: {
            if (state.current_phase == PHASE_SETUP) {
                PlayerID left = static_cast<PlayerID>((me - 1 + N) % N);
                PlayerID right = static_cast<PlayerID>((me + 1) % N);
                STBool demon_nb = eval_is_category(state, left, CAT_DEMON, false, me)
                                | eval_is_category(state, right, CAT_DEMON, false, me);
                if (demon_nb.is_false()) {
                    return;
                }
                if (demon_nb.is_maybe()) {
                    math_misregistration(state, me);
                }
            }
            player.drunklike_char = make_ability(player.claim, ab.first_night);
            player.has_drunklike_char = true;
            drunklike_run_simulation(state, me, yield);
            return;
        }

        case CHAR_Lunatic: {
            for (int i = 0; i < state.puzzle->num_demons; ++i) {
                State substate = state;
                Player& sp = substate.players[me];
                sp.drunklike_char = make_ability(state.puzzle->demons[i], ab.first_night);
                sp.has_drunklike_char = true;
                drunklike_run_simulation(substate, me, yield);
            }
            return;
        }

        case CHAR_FortuneTeller: {
            uint16_t good_team = 0;
            for (PlayerID pid = 0; pid < N; ++pid) {
                if (eval_is_evil(state, pid, me).not_true()) {
                    good_team |= static_cast<uint16_t>(1u << pid);
                }
            }
            uint16_t redherrings = 0;
            for (int night = 1; night <= state.puzzle->max_night; ++night) {
                int16_t ping_idx = get_night_info(state, CHAR_FortuneTeller, me, night);
                if (ping_idx == -1) continue;
                const InfoNode& ping = state.puzzle->info_nodes[ping_idx];
                if (good_team & (1u << ping.player1)) {
                    redherrings |= static_cast<uint16_t>(1u << ping.player1);
                }
                if (good_team & (1u << ping.player2)) {
                    redherrings |= static_cast<uint16_t>(1u << ping.player2);
                }
            }
            uint16_t unchosen_good = good_team & ~redherrings;
            if (unchosen_good != 0) {
                for (PlayerID pid = 0; pid < N; ++pid) {
                    if (unchosen_good & (1u << pid)) {
                        redherrings |= static_cast<uint16_t>(1u << pid);
                        break;
                    }
                }
            }
            for (PlayerID pid = 0; pid < N; ++pid) {
                if (redherrings & (1u << pid)) {
                    State new_state = state;
                    new_state.players[me].character.target = pid;
                    yield(new_state);
                }
            }
            return;
        }

        case CHAR_LordOfTyphon: {
            if (state.current_phase != PHASE_SETUP) {
                yield(state);
                return;
            }
            PlayerID left = static_cast<PlayerID>((me - 1 + N) % N);
            PlayerID right = static_cast<PlayerID>((me + 1) % N);
            if (!state.players[left].is_evil || !state.players[right].is_evil) {
                return;
            }
            int num_evil = 0;
            for (PlayerID pid = 0; pid < N; ++pid) {
                if (state.players[pid].is_evil) num_evil += 1;
            }
            // Check if there is a contiguous run of num_evil evils in the circle
            int run = 0;
            bool found_line = (num_evil == 0);
            for (int i = 0; i < 2 * N; ++i) {
                if (state.players[i % N].is_evil) {
                    run += 1;
                    if (run >= num_evil) {
                        found_line = true;
                        break;
                    }
                } else {
                    run = 0;
                }
            }
            if (found_line) {
                yield(state);
            }
            return;
        }

        case CHAR_Soldier:
        case CHAR_TeaLady:
        case CHAR_Vortox:
            maybe_activate_effects(state, ab, me);
            yield(state);
            return;

        case CHAR_NoDashii: {
            PlayerID fwd_candidates[MAX_PLAYERS];
            PlayerID bkwd_candidates[MAX_PLAYERS];
            int n_fwd = tf_to_droison_in_direction(state, me, 1, fwd_candidates);
            int n_bkwd = tf_to_droison_in_direction(state, me, -1, bkwd_candidates);
            for (int fi = 0; fi < n_fwd; ++fi) {
                for (int bi = 0; bi < n_bkwd; ++bi) {
                    State new_state = state;
                    AbilityInstance& new_nd = new_state.players[me].character;
                    new_nd.target = fwd_candidates[fi];
                    new_nd.aux_target = bkwd_candidates[bi];
                    maybe_activate_effects(new_state, new_nd, me);
                    yield(new_state);
                }
            }
            return;
        }

        case CHAR_VillageIdiot: {
            PlayerID vis[MAX_PLAYERS];
            int n_vis = 0;
            bool already_done = false;
            for (PlayerID pid = 0; pid < N; ++pid) {
                if (has_ability(state.players[pid], CHAR_VillageIdiot)) {
                    vis[n_vis++] = pid;
                    if (state.players[pid].character.self_droison) {
                        already_done = true;
                    }
                }
            }
            if (n_vis <= 1 || already_done) {
                yield(state);
                return;
            }
            for (int i = 0; i < n_vis; ++i) {
                State new_state = state;
                Player& drunk_vi = new_state.players[vis[i]];
                drunk_vi.droison_count += 1;
                drunk_vi.character.self_droison = true;
                yield(new_state);
            }
            return;
        }

        case CHAR_EvilTwin: {
            int8_t night_idx = (state.current_phase == PHASE_NIGHT) ? state.night
                             : (state.current_phase == PHASE_DAY)   ? static_cast<int8_t>(state.day + 1)
                                                                    : static_cast<int8_t>(1);
            STBool i_am_evil = eval_is_evil(state, me, me);
            uint8_t ext_count = (night_idx > 0 && night_idx < MAX_NIGHTS)
                ? state.puzzle->external_info_count[night_idx][CHAR_EvilTwin]
                : 0;
            const ExternalInfoEntry* ext_entries = state.puzzle->external_info[night_idx][CHAR_EvilTwin];
            for (PlayerID pid = 0; pid < N; ++pid) {
                if ((eval_is_evil(state, pid, me) == i_am_evil).is_true()) {
                    continue;
                }
                bool claims_good_twin = false;
                for (uint8_t i = 0; i < ext_count; ++i) {
                    const InfoNode& node = state.puzzle->info_nodes[ext_entries[i].info_node_idx];
                    if (ext_entries[i].player_id == pid && node.player1 == me) {
                        claims_good_twin = true;
                        break;
                    }
                }
                if (!(claims_good_twin || behaves_evil(state, pid))) {
                    continue;
                }
                State new_state = state;
                new_state.players[me].character.target = pid;
                yield(new_state);
            }
            return;
        }

        case CHAR_Puzzlemaster: {
            for (PlayerID pid = 0; pid < N; ++pid) {
                State new_state = state;
                AbilityInstance& pm = new_state.players[me].character;
                pm.target = pid;
                maybe_activate_effects(new_state, pm, me, REASON_SETUP);
                yield(new_state);
            }
            return;
        }

        case CHAR_Xaan: {
            int x_count = 0;
            for (PlayerID pid = 0; pid < N; ++pid) {
                if (is_category(state.players[pid].character.type, CAT_OUTSIDER)) {
                    x_count += 1;
                }
            }
            ab.choice_night = static_cast<int8_t>(x_count);
            yield(state);
            return;
        }

        default:
            yield(state);
            return;
    }
}

void snakecharmer_jump(State& state, PlayerID target, PlayerID me, YieldFn yield) {
    bool i_am_evil = state.players[me].is_evil;
    bool target_is_evil = state.players[target].is_evil;
    CharacterID demon_character = state.players[target].character.type;
    CharacterID my_character = state.players[me].character.type;

    auto step1 = [&](State& s1) {
        auto step2 = [&](State& s2) {
            auto step3 = [&](State& s3) {
                auto step4 = [&](State& s4) {
                    AbilityInstance& new_sc = s4.players[target].character;
                    new_sc.self_droison = true;
                    maybe_activate_effects(s4, new_sc, target);
                    yield(s4);
                };
                change_character(s3, target, my_character, make_yield(step4));
            };
            change_character(s2, me, demon_character, make_yield(step3));
        };
        change_alignment(s1, me, target_is_evil, make_yield(step2));
    };
    change_alignment(state, target, i_am_evil, make_yield(step1));
}

void pukka_do_kill(State& state, PlayerID me, PlayerID target, YieldFn yield) {
    if (target == NONE_PLAYER) {
        yield(state);
        return;
    }
    auto after_attack = [&](State& substate) {
        undroison_player(substate, target, me);
        yield(substate);
    };
    attacked_at_night(state, target, me, make_yield(after_attack));
}

void run_character_night(State& state, PlayerID me, YieldFn yield) {
    Player& player = state.players[me];
    AbilityInstance& ab = player.character;
    int N = state.puzzle->num_players;

    if (CHAR_META[ab.type].is_drunklike) {
        if (ab.type == CHAR_Lunatic) {
            if (is_droisoned(state, ab, me) && state.night == ab.first_night) {
                math_misregistration(state, me);
            }
            auto on_lunatic = [&](State& substate) {
                Player& lunatic = substate.players[me];
                if (lunatic.woke_tonight && is_droisoned(substate, lunatic.character, me)) {
                    STBool tm = STBoolVal::TRUE_MAYBE;
                    math_misregistration(substate, me, &tm);
                }
                yield(substate);
            };
            drunklike_run_simulation(state, me, make_yield(on_lunatic));
            return;
        }
        drunklike_run_simulation(state, me, yield);
        return;
    }

    switch (ab.type) {
        case CHAR_Balloonist: {
            int16_t ping_idx = get_night_info(state, CHAR_Balloonist, me, state.night);
            if (player.is_dead || ping_idx == -1 || lies_about_info(state, me)) {
                ab.prev_category = 0;
                yield(state);
                return;
            }
            const InfoNode& ping = state.puzzle->info_nodes[ping_idx];
            const Player& ping_player = state.players[ping.player1];
            uint8_t current_cat = get_category(ping_player.character.type);
            uint8_t possible_regs = current_cat | get_misreg_categories(state, ping_player, false);
            if (ab.prev_category != 0 && ab.prev_regs_mask != 0 && (ab.prev_regs_mask & (ab.prev_regs_mask - 1)) == 0) {
                possible_regs &= ~ab.prev_regs_mask;
            }
            bool actually_same = (current_cat == ab.prev_category);
            uint8_t prev_cat = ab.prev_category;

            ab.prev_category = current_cat;
            ab.prev_regs_mask = possible_regs;

            if (prev_cat == 0) {
                yield(state);
                return;
            }
            if (state.vortox) {
                if (actually_same) {
                    yield(state);
                }
                return;
            }
            if (possible_regs != 0) {
                if (actually_same) {
                    math_misregistration(state, me);
                }
                yield(state);
                return;
            } else if (is_droisoned(state, ab, me)) {
                math_misregistration(state, me);
                yield(state);
                return;
            }
            return;
        }

        case CHAR_Leviathan: {
            if (state.night < 6 || player.is_dead) {
                yield(state);
            } else if (is_droisoned(state, ab, me)) {
                math_misregistration(state, me);
                yield(state);
            }
            return;
        }

        case CHAR_Poisoner: {
            if (player.is_dead && !ab.vigormortised) {
                yield(state);
                return;
            }
            for (PlayerID target = 0; target < N; ++target) {
                State new_state = state;
                Player& np = new_state.players[me];
                np.character.target = target;
                if (np.history_len < MAX_NIGHTS) {
                    np.target_history[np.history_len++] = target;
                }
                maybe_activate_effects(new_state, np.character, me);
                yield(new_state);
            }
            return;
        }

        case CHAR_Imp: {
            if (state.night == 1 || player.is_dead || player.exorcised_count > 0) {
                yield(state);
                return;
            }
            bool sunk_a_kill = false;
            for (PlayerID target = 0; target < N; ++target) {
                if (target == me) continue;
                if (state.players[target].is_dead) {
                    if (sunk_a_kill) continue;
                    sunk_a_kill = true;
                }
                State new_state = state;
                if (is_droisoned(state, ab, me)) {
                    if (!new_state.players[target].is_dead) {
                        math_misregistration(new_state, me);
                    }
                    yield(new_state);
                    continue;
                }
                attacked_at_night(new_state, target, me, yield);
            }

            // Star pass
            STBool safe = safe_from_attacker(state, me, me);
            bool droisoned = is_droisoned(state, ab, me);
            bool cant_starpass = droisoned || safe.is_true();
            bool maybe_starpass = !droisoned && safe.is_maybe();
            if (cant_starpass || maybe_starpass) {
                State failed_state = state;
                math_misregistration(failed_state, me);
                yield(failed_state);
                if (cant_starpass) return;
            }

            PlayerID scarletwomen[MAX_PLAYERS];
            PlayerID other_minions[MAX_PLAYERS];
            int n_sw = 0, n_other = 0;
            for (PlayerID pid = 0; pid < N; ++pid) {
                SWCatchResult sw = scarlet_woman_catches_death(state, me, pid);
                if (sw.catches.is_true()) {
                    scarletwomen[n_sw++] = pid;
                } else if (eval_is_category(state, pid, CAT_MINION, false, me).not_false() && !state.players[pid].is_dead) {
                    other_minions[n_other++] = pid;
                }
            }
            const PlayerID* catchers = (n_sw > 0) ? scarletwomen : other_minions;
            int n_catchers = (n_sw > 0) ? n_sw : n_other;

            for (int i = 0; i < n_catchers; ++i) {
                PlayerID minion = catchers[i];
                State new_state = state;
                if (n_sw > 0) {
                    new_state.players[minion].woke_tonight = true;
                }
                auto after_change = [&](State& substate) {
                    apply_death(substate, me, me, yield);
                };
                change_character(new_state, minion, CHAR_Imp, make_yield(after_change));
            }
            if (n_catchers == 0) {
                State new_state = state;
                apply_death(new_state, me, me, yield);
            }
            return;
        }

        case CHAR_LordOfTyphon:
        case CHAR_Kazali:
        case CHAR_NoDashii:
        case CHAR_Vortox: {
            if (state.night == 1 || player.is_dead || player.exorcised_count > 0) {
                yield(state);
                return;
            }
            PlayerID targets[MAX_PLAYERS];
            int n_targets = generic_demon_get_targets(state, me, targets);
            for (int i = 0; i < n_targets; ++i) {
                PlayerID target = targets[i];
                State new_state = state;
                if (is_droisoned(state, ab, me)) {
                    if (!state.players[target].is_dead) {
                        math_misregistration(new_state, me);
                    }
                    yield(new_state);
                    continue;
                }
                attacked_at_night(new_state, target, me, yield);
            }
            return;
        }

        case CHAR_Pukka: {
            if (player.is_dead) {
                yield(state);
                return;
            }
            if (is_droisoned(state, ab, me)) {
                if (ab.target != NONE_PLAYER && !state.players[ab.target].is_dead) {
                    math_misregistration(state, me);
                }
                yield(state);
                return;
            }
            if (player.exorcised_count > 0) {
                PlayerID old_target = ab.target;
                ab.target = NONE_PLAYER;
                pukka_do_kill(state, me, old_target, yield);
                return;
            }
            PlayerID old_target = ab.target;
            ab.effects_active = false;
            for (PlayerID new_target = 0; new_target < N; ++new_target) {
                State new_state = state;
                Player& np = new_state.players[me];
                np.character.target = new_target;
                if (np.history_len < MAX_NIGHTS) {
                    np.target_history[np.history_len++] = new_target;
                }
                maybe_activate_effects(new_state, np.character, me);
                pukka_do_kill(new_state, me, old_target, yield);
            }
            return;
        }

        case CHAR_Po: {
            if (state.night == 1 || player.is_dead || player.exorcised_count > 0) {
                yield(state);
                return;
            }
            if (!ab.aux_bool) {
                State charge_state = state;
                charge_state.players[me].character.aux_bool = true;
                yield(charge_state);

                bool sunk_a_kill = false;
                for (PlayerID target = 0; target < N; ++target) {
                    bool dead_target = state.players[target].is_dead;
                    if (dead_target) {
                        if (sunk_a_kill) continue;
                        sunk_a_kill = true;
                    }
                    State new_state = state;
                    if (is_droisoned(state, ab, me)) {
                        if (!dead_target) {
                            math_misregistration(new_state, me);
                        }
                        yield(new_state);
                        continue;
                    }
                    attacked_at_night(new_state, target, me, yield);
                }
            } else {
                ab.aux_bool = false;
                if (is_droisoned(state, ab, me)) {
                    math_misregistration(state, me);
                    yield(state);
                    return;
                }
                for (PlayerID k1 = 0; k1 < N; ++k1) {
                    for (PlayerID k2 = k1 + 1; k2 < N; ++k2) {
                        for (PlayerID k3 = k2 + 1; k3 < N; ++k3) {
                            State new_state = state;
                            PlayerID kills[3] = {k1, k2, k3};
                            auto kill_step = [&](State& s, int idx, YieldFn y) {
                                attacked_at_night(s, kills[idx], me, y);
                            };
                            apply_seq(new_state, 0, 3, kill_step, yield);
                        }
                    }
                }
            }
            return;
        }

        case CHAR_Acrobat: {
            int16_t choice_idx = get_night_info(state, CHAR_Acrobat, me, state.night);
            if (choice_idx == -1) {
                yield(state);
            } else if (player.is_dead) {
                return;
            } else if (is_droisoned(state, ab, me)) {
                yield(state);
            } else {
                const InfoNode& choice = state.puzzle->info_nodes[choice_idx];
                const Player& chosen = state.players[choice.player1];
                if (chosen.droison_count > 0 || has_ability(chosen, CHAR_Drunk)) {
                    attacked_at_night(state, me, me, yield);
                } else {
                    yield(state);
                }
            }
            return;
        }

        case CHAR_Gambler: {
            int16_t ping_idx = get_night_info(state, CHAR_Gambler, me, state.night);
            if (player.is_dead || ping_idx == -1) {
                yield(state);
                return;
            }
            const InfoNode& ping = state.puzzle->info_nodes[ping_idx];
            STBool result = eval_is_character(state, ping.player1, ping.character1, me);
            if (result.is_true()) {
                yield(state);
            } else if (result.is_false()) {
                if (is_droisoned(state, ab, me)) {
                    math_misregistration(state, me);
                    yield(state);
                    return;
                }
                attacked_at_night(state, me, me, yield);
            } else if (result.is_maybe()) {
                State live_state = state;
                yield(live_state);
                State die_state = state;
                if (is_droisoned(state, ab, me)) {
                    math_misregistration(die_state, me);
                    yield(die_state);
                    return;
                } else {
                    attacked_at_night(die_state, me, me, yield);
                }
            }
            return;
        }

        case CHAR_Gossip: {
            if (player.is_dead || player.saved_day_num != state.night - 1 || player.saved_day_bool.is_false()) {
                yield(state);
                return;
            }
            bool dud_kill_done = false;
            if (player.saved_day_bool.is_maybe()) {
                State forked = state;
                yield(forked);
                dud_kill_done = true;
            }
            if (is_droisoned(state, ab, me)) {
                math_misregistration(state, me);
                yield(state);
                return;
            }
            for (PlayerID target = 0; target < N; ++target) {
                if (state.players[target].is_dead) {
                    if (dud_kill_done) continue;
                    dud_kill_done = true;
                }
                State new_state = state;
                attacked_at_night(new_state, target, me, yield);
            }
            return;
        }

        case CHAR_Courtier: {
            if (lies_about_info(state, me)) {
                if (player.is_dead || ab.spent) {
                    yield(state);
                    return;
                }
                State no_choice = state;
                yield(no_choice);

                ab.spent = true;
                ab.choice_night = state.night;
                if (is_droisoned(state, ab, me)) {
                    State bad_choice = state;
                    yield(bad_choice);
                    State good_choice = state;
                    math_misregistration(good_choice, me);
                    yield(good_choice);
                    return;
                }
                for (PlayerID target = 0; target < N; ++target) {
                    State new_state = state;
                    AbilityInstance& new_c = new_state.players[me].character;
                    new_c.target = target;
                    maybe_activate_effects(new_state, new_c, me);
                    yield(new_state);
                }
                return;
            }

            int16_t choice_idx = get_night_info(state, CHAR_Courtier, me, state.night);
            if (choice_idx == -1) {
                yield(state);
                return;
            }
            if (player.is_dead || ab.spent) {
                return;
            }
            ab.choice_night = state.night;
            ab.spent = true;
            const InfoNode& choice = state.puzzle->info_nodes[choice_idx];
            PlayerID valid_targets[MAX_PLAYERS];
            int n_valid = 0;
            for (PlayerID target = 0; target < N; ++target) {
                if (eval_is_character(state, target, choice.character1, me).not_false()) {
                    valid_targets[n_valid++] = target;
                }
            }
            if (is_droisoned(state, ab, me)) {
                if (n_valid > 0) {
                    math_misregistration(state, me);
                }
                yield(state);
                return;
            }
            for (int i = 0; i < n_valid; ++i) {
                State new_state = state;
                AbilityInstance& new_c = new_state.players[me].character;
                new_c.target = valid_targets[i];
                maybe_activate_effects(new_state, new_c, me);
                yield(new_state);
            }
            return;
        }

        case CHAR_SnakeCharmer: {
            if (player.is_dead) {
                yield(state);
                return;
            }
            if (lies_about_info(state, me)) {
                STBool demon_queries[MAX_PLAYERS];
                PlayerID maybe_demons[MAX_PLAYERS];
                int n_maybe = 0;
                bool any_not_true = false;
                for (PlayerID t = 0; t < N; ++t) {
                    demon_queries[t] = eval_is_category(state, t, CAT_DEMON, false, me);
                    if (demon_queries[t].not_false()) {
                        maybe_demons[n_maybe++] = t;
                    }
                    if (demon_queries[t].not_true()) {
                        any_not_true = true;
                    }
                }
                if (is_droisoned(state, ab, me) && n_maybe > 0) {
                    State poisoned_state = state;
                    if (!ab.self_droison) {
                        math_misregistration(poisoned_state, me);
                    }
                    yield(poisoned_state);
                    return;
                }
                for (int i = 0; i < n_maybe; ++i) {
                    State jump_state = state;
                    snakecharmer_jump(jump_state, maybe_demons[i], me, yield);
                }
                if (any_not_true) {
                    yield(state);
                }
                return;
            }

            int16_t choice_idx = get_night_info(state, CHAR_SnakeCharmer, me, state.night);
            if (choice_idx == -1) {
                yield(state);
                return;
            }
            const InfoNode& choice = state.puzzle->info_nodes[choice_idx];
            STBool is_demon = eval_is_category(state, choice.player1, CAT_DEMON, false, me);
            if (is_demon.is_false()) {
                yield(state);
                return;
            }
            if (is_demon.is_maybe()) {
                State no_jump = state;
                yield(no_jump);
            }
            State jump_state = state;
            if (is_droisoned(jump_state, jump_state.players[me].character, me)) {
                if (!jump_state.players[me].character.self_droison) {
                    math_misregistration(jump_state, me);
                }
                yield(jump_state);
                return;
            }
            snakecharmer_jump(jump_state, choice.player1, me, yield);
            return;
        }

        case CHAR_NightWatchman: {
            uint8_t ext_count = state.puzzle->external_info_count[state.night][CHAR_NightWatchman];
            const ExternalInfoEntry* ext_entries = state.puzzle->external_info[state.night][CHAR_NightWatchman];

            if (lies_about_info(state, me)) {
                int good_pings = 0;
                for (uint8_t i = 0; i < ext_count; ++i) {
                    const InfoNode& node = state.puzzle->info_nodes[ext_entries[i].info_node_idx];
                    if (node.player1 == me) {
                        good_pings += 1;
                    }
                }
                if (good_pings > 1) {
                    return;
                }
                if (good_pings == 1) {
                    if (!ab.spent) {
                        ab.spent = true;
                        yield(state);
                    }
                    return;
                }
                if (!ab.spent) {
                    State spent_world = state;
                    spent_world.players[me].character.spent = true;
                    yield(spent_world);
                }
                yield(state);
                return;
            }

            int16_t choice_idx = get_night_info(state, CHAR_NightWatchman, me, state.night);
            if (choice_idx == -1) {
                yield(state);
                return;
            }
            if (player.is_dead || ab.spent) {
                return;
            }
            ab.spent = true;
            const InfoNode& choice = state.puzzle->info_nodes[choice_idx];
            if (behaves_evil(state, choice.player1)) {
                if (is_droisoned(state, ab, me)) {
                    math_misregistration(state, me);
                }
                yield(state);
                return;
            }
            bool confirmed_by_good = false;
            for (uint8_t i = 0; i < ext_count; ++i) {
                const InfoNode& node = state.puzzle->info_nodes[ext_entries[i].info_node_idx];
                if (choice.player1 == ext_entries[i].player_id && node.player1 == me) {
                    confirmed_by_good = true;
                    break;
                }
            }
            if (is_droisoned(state, ab, me)) {
                math_misregistration(state, me);
                if (!confirmed_by_good) {
                    yield(state);
                }
            } else if (confirmed_by_good) {
                yield(state);
            }
            return;
        }

        case CHAR_Witch: {
            maybe_deactivate_effects(state, ab, me);
            ab.target = NONE_PLAYER;

            int living_count = 0;
            for (PlayerID pid = 0; pid < N; ++pid) {
                if (!state.players[pid].is_dead) living_count += 1;
            }
            if ((player.is_dead && !ab.vigormortised) || living_count <= 3) {
                yield(state);
                return;
            }
            if (is_droisoned(state, ab, me)) {
                STBool tm = STBoolVal::TRUE_MAYBE;
                math_misregistration(state, me, &tm);
                yield(state);
                return;
            }

            PlayerID nominators[MAX_PLAYERS * 2];
            int n_nom = 0;
            uint16_t nom_mask = 0;
            int ev_count = state.puzzle->day_event_counts[state.night];
            const EventNode* evs = state.puzzle->day_events[state.night];
            for (int i = 0; i < ev_count; ++i) {
                if (evs[i].type == EVENT_DIES && evs[i].flag != 0) {
                    nominators[n_nom++] = evs[i].player;
                    nom_mask |= static_cast<uint16_t>(1u << evs[i].player);
                } else if (evs[i].type == EVENT_UNEVENTFUL_NOMINATION) {
                    nominators[n_nom++] = evs[i].target;
                    nom_mask |= static_cast<uint16_t>(1u << evs[i].target);
                } else if (evs[i].type == EVENT_TOWNCRIER_NOMINATORS) {
                    for (int k = 0; k < evs[i].count; ++k) {
                        nominators[n_nom++] = evs[i].players[k];
                        nom_mask |= static_cast<uint16_t>(1u << evs[i].players[k]);
                    }
                }
            }
            for (int i = 0; i < n_nom; ++i) {
                PlayerID target = nominators[i];
                State new_state = state;
                AbilityInstance& new_witch = new_state.players[me].character;
                new_witch.target = target;
                maybe_activate_effects(new_state, new_witch, me);
                yield(new_state);
            }
            for (PlayerID target = 0; target < N; ++target) {
                if (!(nom_mask & (1u << target))) {
                    ab.target = target;
                    maybe_activate_effects(state, ab, me);
                    yield(state);
                    return;
                }
            }
            return;
        }

        case CHAR_Xaan: {
            if ((player.is_dead && !ab.vigormortised) || state.night != ab.choice_night) {
                ab.aux_bool = false;
                ab.aux_mask = 0;
                yield(state);
                return;
            }
            uint16_t trues_mask = 0;
            PlayerID maybes[MAX_PLAYERS];
            int n_maybes = 0;
            for (PlayerID pid = 0; pid < N; ++pid) {
                STBool is_tf = eval_is_category(state, pid, CAT_TOWNSFOLK, false, me);
                if (is_tf.is_true()) {
                    trues_mask |= static_cast<uint16_t>(1u << pid);
                } else if (is_tf.is_maybe()) {
                    maybes[n_maybes++] = pid;
                }
            }
            if (is_droisoned(state, ab, me) && trues_mask != 0) {
                math_misregistration(state, me);
            }
            int num_subsets = 1 << n_maybes;
            for (int mask = 1; mask < num_subsets; ++mask) {
                uint16_t subset_mask = trues_mask;
                for (int b = 0; b < n_maybes; ++b) {
                    if (mask & (1 << b)) {
                        subset_mask |= static_cast<uint16_t>(1u << maybes[b]);
                    }
                }
                State new_state = state;
                AbilityInstance& new_xaan = new_state.players[me].character;
                new_xaan.aux_bool = true;
                new_xaan.aux_mask = subset_mask;
                maybe_activate_effects(new_state, new_xaan, me);
                yield(new_state);
            }
            ab.aux_bool = true;
            ab.aux_mask = trues_mask;
            maybe_activate_effects(state, ab, me);
            yield(state);
            return;
        }

        case CHAR_Ravenkeeper:
        case CHAR_Sage: {
            if (default_info_check(state, ab, me, true, true)) {
                yield(state);
            }
            return;
        }

        default: {
            if (default_info_check(state, ab, me, false, false)) {
                yield(state);
            }
            return;
        }
    }
}

void run_character_day(State& state, PlayerID me, YieldFn yield) {
    Player& player = state.players[me];
    AbilityInstance& ab = player.character;

    if (ab.type == CHAR_Savant) {
        int16_t ping_idx = get_day_info(state, CHAR_Savant, me);
        if (player.is_dead || ping_idx == -1 || lies_about_info(state, me)) {
            yield(state);
            return;
        }
        STBool result = eval_info(state, ping_idx, me);
        if (state.vortox) {
            if (!result.truth()) {
                math_misregistration(state, me);
                yield(state);
            }
            return;
        }
        if (is_droisoned(state, ab, me)) {
            math_misregistration(state, me, &result);
            yield(state);
        } else if (result.not_false()) {
            yield(state);
        }
        return;
    }

    if (ab.type == CHAR_Mutant) {
        if (player.is_dead || state.day != state.puzzle->max_day) {
            yield(state);
        } else if (!is_category(player.claim, CAT_OUTSIDER)) {
            yield(state);
        } else if (is_droisoned(state, ab, me)) {
            STBool fm = STBoolVal::FALSE_MAYBE;
            math_misregistration(state, me, &fm);
            yield(state);
        }
        return;
    }

    if (default_info_check(state, ab, me, false, false)) {
        yield(state);
    }
}

void run_character_end_night(State& state, PlayerID me, YieldFn yield) {
    Player& player = state.players[me];
    AbilityInstance& ab = player.character;

    switch (ab.type) {
        case CHAR_Drunk:
            change_claim_if_claimed_change_tonight(state, me);
            if (is_category(player.claim, CAT_TOWNSFOLK) || lies_about_character(state, me, true)) {
                yield(state);
            }
            return;
        case CHAR_Monk:
            maybe_deactivate_effects(state, ab, me);
            ab.target = NONE_PLAYER;
            yield(state);
            return;
        default:
            yield(state);
            return;
    }
}

void run_character_end_day(State& state, PlayerID me, YieldFn yield) {
    Player& player = state.players[me];
    AbilityInstance& ab = player.character;

    switch (ab.type) {
        case CHAR_Poisoner:
        case CHAR_Cerenovus:
            maybe_deactivate_effects(state, ab, me);
            ab.target = NONE_PLAYER;
            yield(state);
            return;
        case CHAR_Courtier:
            if (ab.target != NONE_PLAYER && (state.day - ab.choice_night) >= 2) {
                maybe_deactivate_effects(state, ab, me);
                ab.target = NONE_PLAYER;
            }
            yield(state);
            return;
        case CHAR_Princess:
            if (ab.first_night < state.day) {
                maybe_deactivate_effects(state, ab, me);
                ab.aux_bool = false;
            }
            yield(state);
            return;
        case CHAR_Xaan:
            if (ab.aux_bool) {
                maybe_deactivate_effects(state, ab, me);
                ab.aux_bool = false;
                ab.aux_mask = 0;
            }
            yield(state);
            return;
        case CHAR_Vortox: {
            int ev_count = state.puzzle->day_event_counts[state.day];
            const EventNode* evs = state.puzzle->day_events[state.day];
            for (int i = 0; i < ev_count; ++i) {
                if (evs[i].type == EVENT_EXECUTION || evs[i].type == EVENT_EXECUTION_BY_ST) {
                    yield(state);
                    return;
                }
            }
            return;
        }
        default:
            yield(state);
            return;
    }
}

bool global_end_night_check(const State& state, CharacterID char_t) {
    if (char_t == CHAR_NightWatchman) {
        for (PlayerID pid = 0; pid < state.puzzle->num_players; ++pid) {
            if (get_night_info(state, CHAR_NightWatchman, pid, state.night) != -1
                && !has_ability(state.players[pid], CHAR_NightWatchman)
                && !lies_about_info(state, pid)) {
                return false;
            }
        }
    }
    return true;
}

// Phase & Event runners on State
void run_all_players_with_currently_acting_character(State& state, YieldFn yield) {
    if (state.num_players_still_to_act == 0) {
        yield(state);
        return;
    }

    PlayerID pid = state.players_still_to_act[--state.num_players_still_to_act];
    Player& player = state.players[pid];
    AbilityInstance* ab = get_ability_that_acts_like(player, state.currently_acting_character);
    if (ab == nullptr) {
        return;
    }

    auto recurse = [&](State& substate) {
        run_all_players_with_currently_acting_character(substate, yield);
    };
    YieldFn next_yield = make_yield(recurse);

    switch (state.current_phase) {
        case PHASE_NIGHT:
            if (wakes_tonight_ability(state, *ab, pid)) {
                player.woke_tonight = true;
            }
            run_character_night(state, pid, next_yield);
            break;
        case PHASE_DAY:
            run_character_day(state, pid, next_yield);
            break;
        case PHASE_SETUP:
            run_character_setup(state, pid, next_yield);
            break;
    }
}

bool check_external_night_info(State& state, CharacterID char_t, int8_t night) {
    if (night <= 0 || night >= MAX_NIGHTS) return true;
    uint8_t count = state.puzzle->external_info_count[night][char_t];
    for (uint8_t i = 0; i < count; ++i) {
        const ExternalInfoEntry& entry = state.puzzle->external_info[night][char_t][i];
        PlayerID pid = entry.player_id;
        if (behaves_evil(state, pid)) continue;
        const InfoNode& node = state.puzzle->info_nodes[entry.info_node_idx];
        bool ok = false;
        switch (node.type) {
            case EXTINFO_WIDOW_IN_PLAY:
                ok = true;
                break;
            case EXTINFO_EVILTWIN_IS: {
                const AbilityInstance* et = get_ability(state.players[node.player1], CHAR_EvilTwin);
                ok = (et != nullptr && et->target == pid);
                break;
            }
            case EXTINFO_NIGHTWATCHMAN_PING: {
                PlayerID nwm_id = node.player1;
                const Player& nwm = state.players[nwm_id];
                int16_t choice_idx = get_night_info(state, CHAR_NightWatchman, nwm_id, state.night);
                bool chose_me = (choice_idx != -1 && state.puzzle->info_nodes[choice_idx].player1 == pid);
                bool nwm_truthful = !lies_about_info(state, nwm_id);
                const AbilityInstance* ab = get_ability(nwm, CHAR_NightWatchman);
                ok = !(ab == nullptr || is_droisoned(state, *ab, nwm_id) || (!chose_me && nwm_truthful));
                break;
            }
            default:
                ok = true;
                break;
        }
        if (!ok) return false;
    }
    return true;
}

void run_next_character(State& state, YieldFn yield) {
    const SerializedPuzzle& puzzle = *state.puzzle;
    const CharacterID* order = (state.current_phase == PHASE_NIGHT) ? puzzle.night_order
                             : (state.current_phase == PHASE_DAY)   ? puzzle.day_order
                                                                    : puzzle.setup_order;
    uint8_t order_len = (state.current_phase == PHASE_NIGHT) ? puzzle.num_night_order
                      : (state.current_phase == PHASE_DAY)   ? puzzle.num_day_order
                                                             : puzzle.num_setup_order;

    if (state.phase_order_index >= order_len) {
        yield(state);
        return;
    }

    CharacterID character_t = order[state.phase_order_index];
    state.currently_acting_character = character_t;
    state.num_players_still_to_act = 0;
    uint16_t acting_mask = 0;
    for (PlayerID pid = 0; pid < puzzle.num_players; ++pid) {
        if (ability_acts_like(state.players[pid], character_t)) {
            state.players_still_to_act[state.num_players_still_to_act++] = pid;
            acting_mask |= static_cast<uint16_t>(1u << pid);
        }
    }

    // Make sure no good players incorrectly claim to act as this character
    for (PlayerID pid = 0; pid < puzzle.num_players; ++pid) {
        int16_t ping_idx = (state.night != 0)
            ? get_night_info(state, character_t, pid, state.night)
            : get_day_info(state, character_t, pid);
        if (ping_idx != -1 && !(acting_mask & (1u << pid)) && !lies_about_info(state, pid)) {
            return;
        }
    }

    auto after_players = [&](State& substate) {
        if (substate.current_phase == PHASE_NIGHT) {
            if (!check_external_night_info(substate, substate.currently_acting_character, substate.night)) {
                return;
            }
        }
        substate.phase_order_index += 1;
        yield(substate);
    };
    run_all_players_with_currently_acting_character(state, make_yield(after_players));
}

void end_setup(State& state, YieldFn yield) {
    for (PlayerID pid = 0; pid < state.puzzle->num_players; ++pid) {
        const Player& p = state.players[pid];
        if (p.character.type != p.claim && !lies_about_character(state, pid)) {
            return;
        }
    }
    state.current_phase = PHASE_NIGHT;
    state.phase_order_index = 0;
    state.night = 1;
    state.day = 0;
    yield(state);
}

void finish_end_night(State& state, YieldFn yield) {
    const SerializedPuzzle& puzzle = *state.puzzle;
    int N = puzzle.num_players;

    for (int i = 0; i < puzzle.num_script; ++i) {
        if (!global_end_night_check(state, puzzle.script[i])) {
            return;
        }
    }
    for (PlayerID pid = 0; pid < N; ++pid) {
        state.players[pid].woke_tonight = false;
    }

    // Check the right people have Died / Resurrected in the night
    uint16_t currently_alive_mask = 0;
    for (PlayerID pid = 0; pid < N; ++pid) {
        if (eval_is_alive(state, pid, NONE_PLAYER).is_true()) {
            currently_alive_mask |= static_cast<uint16_t>(1u << pid);
        }
    }
    uint16_t currently_alive_gt = state.previously_alive_mask;
    uint8_t nd_count = puzzle.night_death_counts[state.night];
    for (uint8_t i = 0; i < nd_count; ++i) {
        const NightDeathNode& death = puzzle.night_deaths[state.night][i];
        bool prev_alive_gt = !death.is_resurrection;
        bool was_alive = (state.previously_alive_mask & (1u << death.player)) != 0;
        if (was_alive != prev_alive_gt) {
            return;
        }
        if (prev_alive_gt) {
            currently_alive_gt &= ~static_cast<uint16_t>(1u << death.player);
        } else {
            currently_alive_gt |= static_cast<uint16_t>(1u << death.player);
        }
    }
    if (currently_alive_mask != currently_alive_gt) {
        return;
    }

    // Check good players are what they claim to be. Update claim if changed.
    for (PlayerID pid = 0; pid < N; ++pid) {
        change_claim_if_claimed_change_tonight(state, pid);
        if (state.players[pid].character.type != state.players[pid].claim
            && !lies_about_character(state, pid)) {
            return;
        }
    }

    int count = 0;
    for (PlayerID pid = 0; pid < N; ++pid) {
        if (state.tomorrow_math_misreg_mask & (1u << pid)) {
            count += 1;
        }
    }
    state.math_misreg_bounds[0] = count;
    state.math_misreg_bounds[1] = count;
    state.math_misregisterers_mask = state.tomorrow_math_misreg_mask;
    state.tomorrow_math_misreg_mask = 0;

    state.current_phase = PHASE_DAY;
    state.phase_order_index = 0;
    state.day = state.night;
    state.night = 0;
    yield(state);
}

void end_night(State& state, YieldFn yield) {
    int N = state.puzzle->num_players;
    auto per_player = [&](State& s, int pid, YieldFn y) {
        run_character_end_night(s, static_cast<PlayerID>(pid), y);
    };
    auto after_players = [&](State& s) {
        finish_end_night(s, yield);
    };
    apply_seq(state, 0, N, per_player, make_yield(after_players));
}

void finish_end_day(State& state, YieldFn yield) {
    int N = state.puzzle->num_players;
    uint16_t alive_mask = 0;
    for (PlayerID pid = 0; pid < N; ++pid) {
        if (eval_is_alive(state, pid, NONE_PLAYER).is_true()) {
            alive_mask |= static_cast<uint16_t>(1u << pid);
        }
    }
    state.previously_alive_mask = alive_mask;
    state.current_phase = PHASE_NIGHT;
    state.phase_order_index = 0;
    state.night = state.day + 1;
    state.day = 0;
    yield(state);
}

void end_day(State& state, YieldFn yield) {
    int N = state.puzzle->num_players;
    auto per_player = [&](State& s, int pid, YieldFn y) {
        run_character_end_day(s, static_cast<PlayerID>(pid), y);
    };
    auto after_players = [&](State& s) {
        finish_end_day(s, yield);
    };
    apply_seq(state, 0, N, per_player, make_yield(after_players));
}

void run_event(State& state, int round, int event_idx, YieldFn yield) {
    const EventNode& ev = state.puzzle->day_events[round][event_idx];
    switch (ev.type) {
        case EVENT_EXECUTION:
            char_executed(state, ev.player, ev.flag != 0, yield);
            return;

        case EVENT_EXECUTION_BY_ST: {
            if (ev.target != NONE_PLAYER) {
                Player& nominee = state.players[ev.target];
                AbilityInstance* virgin_ab = get_ability(nominee, CHAR_Virgin);
                if (virgin_ab != nullptr) {
                    STBool tf_nom = eval_is_category(state, ev.player, CAT_TOWNSFOLK, false, ev.target);
                    if (nominee.is_dead || is_droisoned(state, *virgin_ab, ev.target) || virgin_ab->spent || tf_nom.is_false()) {
                        return;
                    }
                    virgin_ab->spent = true;
                    if (!tf_nom.truth()) {
                        math_misregistration(state, ev.target);
                    }
                    char_executed(state, ev.player, ev.flag != 0, yield);
                }
            }
            return;
        }

        case EVENT_UNEVENTFUL_NOMINATION: {
            PlayerID nominator = ev.target;
            PlayerID nominee = ev.player;
            if (AbilityInstance* princess = get_ability(state.players[nominator], CHAR_Princess)) {
                if (princess->first_night == state.day) {
                    int ev_count = state.puzzle->day_event_counts[state.day];
                    const EventNode* evs = state.puzzle->day_events[state.day];
                    for (int i = 0; i < ev_count; ++i) {
                        if ((evs[i].type == EVENT_EXECUTION || evs[i].type == EVENT_EXECUTION_BY_ST) && evs[i].player == nominee) {
                            princess->aux_bool = true;
                            maybe_activate_effects(state, *princess, nominator);
                            break;
                        }
                    }
                }
            }
            if (AbilityInstance* golem = get_ability(state.players[nominator], CHAR_Golem)) {
                golem->spent = true;
                STBool is_demon = eval_is_category(state, nominee, CAT_DEMON, false, nominator);
                if (is_demon.is_false() && is_droisoned(state, *golem, nominator)) {
                    math_misregistration(state, nominator);
                } else if (is_demon.is_maybe()) {
                    if (is_category(state.players[nominee].character.type, CAT_DEMON)) {
                        math_misregistration(state, nominator);
                    }
                } else if (!is_demon.is_true()) {
                    return;
                }
            }
            if (AbilityInstance* virgin = get_ability(state.players[nominee], CHAR_Virgin)) {
                STBool nominator_is_tf = eval_is_category(state, nominator, CAT_TOWNSFOLK, false, nominee);
                if (state.players[nominee].is_dead || virgin->spent || nominator_is_tf.not_true()) {
                    virgin->spent = true;
                    if (!nominator_is_tf.truth()) {
                        math_misregistration(state, nominee);
                    }
                } else if (is_droisoned(state, *virgin, nominee)) {
                    math_misregistration(state, nominee);
                    virgin->spent = true;
                } else {
                    return;
                }
            }
            for (PlayerID pid = 0; pid < state.puzzle->num_players; ++pid) {
                if (AbilityInstance* witch = get_ability(state.players[pid], CHAR_Witch)) {
                    if (witch->target != nominator) {
                        // unaffected
                    } else if (safe_from_attacker(state, nominator, pid).not_false()) {
                        math_misregistration(state, pid);
                    } else {
                        return;
                    }
                    break;
                }
            }
            yield(state);
            return;
        }

        case EVENT_DIES: {
            if (ev.flag != 0) {
                Player& dying = state.players[ev.player];
                PlayerID wid = dying.witch_cursed;
                if (wid != NONE_PLAYER) {
                    char_killed(state, ev.player, wid, yield);
                }
            } else if (ev.target != NONE_PLAYER) {
                PlayerID nominator = ev.target;
                if (state.rioting_count > 0) {
                    PlayerID riot_id = NONE_PLAYER;
                    for (PlayerID pid = 0; pid < state.puzzle->num_players; ++pid) {
                        if (!state.players[pid].is_dead
                            && has_ability(state.players[pid], CHAR_Riot)
                            && !is_droisoned(state, state.players[pid].character, pid)) {
                            riot_id = pid;
                            break;
                        }
                    }
                    if (riot_id != NONE_PLAYER) {
                        if (state.players[ev.player].is_dead) {
                            yield(state);
                        } else {
                            char_killed(state, ev.player, riot_id, yield);
                        }
                    }
                } else if (AbilityInstance* golem = get_ability(state.players[nominator], CHAR_Golem)) {
                    golem->spent = true;
                    STBool is_demon = eval_is_category(state, ev.player, CAT_DEMON, false, nominator);
                    if (!is_droisoned(state, *golem, nominator) && is_demon.not_true()) {
                        if (is_category(state.players[ev.player].character.type, CAT_DEMON)) {
                            math_misregistration(state, nominator);
                        }
                        char_killed(state, ev.player, nominator, yield);
                    }
                }
            }
            return;
        }

        case EVENT_SLAYER_SHOT: {
            Player& shooter = state.players[ev.player];
            AbilityInstance* ab = get_ability(shooter, CHAR_Slayer);
            bool died = (ev.flag != 0);
            if (ab == nullptr) {
                if (lies_about_character(state, ev.player) && !died) {
                    yield(state);
                }
                return;
            }
            Player& target = state.players[ev.target];
            STBool should_die = (shooter.is_dead || target.is_dead || ab->spent)
                ? STBoolVal::FALSE
                : eval_is_category(state, ev.target, CAT_DEMON, false, ev.player);
            if (is_droisoned(state, *ab, shooter.id)) {
                if (should_die.not_false() && !died) {
                    STBool inv = ~should_die;
                    math_misregistration(state, ev.player, &inv);
                }
                should_die = STBoolVal::FALSE;
            }
            ab->spent = true;
            if (died && should_die.not_false()) {
                math_misregistration(state, ev.player, &should_die);
                char_killed(state, ev.target, shooter.id, yield);
            } else if (!died && should_die.not_true()) {
                yield(state);
            }
            return;
        }

        case EVENT_JUGGLER_JUGGLE: {
            Player& juggler = state.players[ev.player];
            juggler.num_juggles = ev.count;
            for (int i = 0; i < ev.count; ++i) {
                juggler.correct_juggles[i] = eval_is_character(state, ev.players[i], ev.characters[i], ev.player);
            }
            yield(state);
            return;
        }

        case EVENT_DOOMSAYER_CALL: {
            STBool a = eval_is_evil(state, ev.player, ev.player);
            STBool b = eval_is_evil(state, ev.target, ev.player);
            if (!(a ^ b).is_true()) {
                char_killed(state, ev.target, NONE_PLAYER, yield);
            }
            return;
        }

        case EVENT_GOSSIP_GOSSIP: {
            Player& gossip = state.players[ev.player];
            gossip.saved_day_bool = eval_info(state, ev.info_node_idx, ev.player);
            gossip.saved_day_num = state.day;
            yield(state);
            return;
        }

        case EVENT_KLUTZ_CHOICE: {
            Player& klutz_player = state.players[ev.player];
            AbilityInstance* klutz_ab = get_ability(klutz_player, CHAR_Klutz);
            if (klutz_ab == nullptr) {
                if (lies_about_character(state, ev.player)) {
                    yield(state);
                }
                return;
            }
            STBool is_good = ~eval_is_evil(state, ev.target, ev.player);
            if (is_good.is_true()) {
                yield(state);
            } else if (is_droisoned(state, *klutz_ab, ev.player)) {
                math_misregistration(state, ev.player, &is_good);
                yield(state);
            }
            return;
        }

        default:
            yield(state);
            return;
    }
}

// Starting configuration & speculation logic (matches solve.py)
struct StartingConfig {
    uint8_t num_liars = 0;
    CharacterID liar_characters[MAX_PLAYERS];
    PlayerID liar_positions[MAX_PLAYERS];

    uint16_t speculative_evil_mask = 0;
    uint16_t speculative_good_mask = 0;
    uint16_t speculative_ceremad_mask = 0;
};

void world_check(const SerializedPuzzle& puzzle, const StartingConfig& config, YieldFn yield);

void round_robin(State& state, const StartingConfig& config, YieldFn yield) {
    int N = state.puzzle->num_players;
    bool any_spec_good = false;
    for (PlayerID pid = 0; pid < N; ++pid) {
        Player& p = state.players[pid];
        if (p.speculative_evil) {
            p.speculative_evil = false;
            if (!behaves_evil(state, pid)) {
                return;
            }
        }
        if (p.speculative_ceremad) {
            if (p.ceremad == 0 || p.character.type == p.claim) {
                return;
            }
        }
        if (p.speculative_good) {
            any_spec_good = true;
        }
    }

    if (!any_spec_good) {
        uint16_t spec_good_mask = 0;
        for (PlayerID pid = 0; pid < N; ++pid) {
            if (state.players[pid].ever_behaved_evil && !behaves_evil(state, pid)) {
                spec_good_mask |= static_cast<uint16_t>(1u << pid);
            }
        }
        if (spec_good_mask != 0) {
            StartingConfig redo = config;
            redo.speculative_good_mask = spec_good_mask;
            world_check(*state.puzzle, redo, yield);
            return;
        }
    }
    yield(state);
}

enum SimStepType : uint8_t {
    STEP_RUN_NEXT_CHAR = 0,
    STEP_END_SETUP,
    STEP_END_NIGHT,
    STEP_RUN_EVENT,
    STEP_END_DAY,
    STEP_ROUND_ROBIN,
};

struct SimStep {
    SimStepType type;
    uint8_t round;
    uint8_t event_idx;
};

struct SimSchedule {
    int num_steps = 0;
    SimStep steps[MAX_STEPS];
};

SimSchedule build_schedule(const SerializedPuzzle& puzzle) {
    SimSchedule sched{};
    auto push = [&](SimStepType t, uint8_t r = 0, uint8_t e = 0) {
        sched.steps[sched.num_steps++] = SimStep{t, r, e};
    };

    for (int i = 0; i < puzzle.num_setup_order; ++i) {
        push(STEP_RUN_NEXT_CHAR);
    }
    push(STEP_END_SETUP);

    for (uint8_t round = 1; round <= puzzle.max_night; ++round) {
        for (int i = 0; i < puzzle.num_night_order; ++i) {
            push(STEP_RUN_NEXT_CHAR);
        }
        push(STEP_END_NIGHT);
        if (round <= puzzle.max_day) {
            for (int i = 0; i < puzzle.num_day_order; ++i) {
                push(STEP_RUN_NEXT_CHAR);
            }
            for (uint8_t ev = 0; ev < puzzle.day_event_counts[round]; ++ev) {
                push(STEP_RUN_EVENT, round, ev);
            }
            if (round < puzzle.max_day || puzzle.finish_final_day) {
                push(STEP_END_DAY);
            }
        }
    }
    push(STEP_ROUND_ROBIN);
    return sched;
}

void run_schedule(
    State& state,
    const SimSchedule& sched,
    int step_idx,
    const StartingConfig& config,
    YieldFn solution_yield
) {
    if (step_idx >= sched.num_steps) {
        solution_yield(state);
        return;
    }
    auto next = [&](State& substate) {
        run_schedule(substate, sched, step_idx + 1, config, solution_yield);
    };
    YieldFn next_yield = make_yield(next);
    const SimStep& step = sched.steps[step_idx];
    switch (step.type) {
        case STEP_RUN_NEXT_CHAR:
            run_next_character(state, next_yield);
            break;
        case STEP_END_SETUP:
            end_setup(state, next_yield);
            break;
        case STEP_END_NIGHT:
            end_night(state, next_yield);
            break;
        case STEP_RUN_EVENT:
            run_event(state, step.round, step.event_idx, next_yield);
            break;
        case STEP_END_DAY:
            end_day(state, next_yield);
            break;
        case STEP_ROUND_ROBIN:
            round_robin(state, config, next_yield);
            break;
    }
}

bool begin_game(State& state, bool allow_duplicate_tokens_in_bag) {
    int N = state.puzzle->num_players;
    state.current_phase = PHASE_SETUP;
    state.phase_order_index = 0;
    update_character_callbacks(state);
    for (PlayerID pid = 0; pid < N; ++pid) {
        state.initial_characters[pid] = state.players[pid].character.type;
    }
    state.night = 0;
    state.day = 0;
    state.previously_alive_mask = static_cast<uint16_t>((1u << N) - 1u);
    state.math_misreg_bounds[0] = 0;
    state.math_misreg_bounds[1] = 0;
    state.math_misregisterers_mask = 0;
    state.tomorrow_math_misreg_mask = 0;
    state.vortox = false;

    if (!allow_duplicate_tokens_in_bag) {
        uint64_t good_claims_lo = 0;
        uint64_t good_claims_hi = 0;
        for (PlayerID pid = 0; pid < N; ++pid) {
            const Player& p = state.players[pid];
            if (behaves_evil(state, pid)
                || (CHAR_META[p.character.type].lies_about_character_and_info
                    && !draws_wrong_token(p.character.type))) {
                continue;
            }
            uint8_t cid = p.claim;
            if (cid < 64) {
                if (good_claims_lo & (1ULL << cid)) return false;
                good_claims_lo |= (1ULL << cid);
            } else {
                if (good_claims_hi & (1ULL << (cid - 64))) return false;
                good_claims_hi |= (1ULL << (cid - 64));
            }
        }
    }
    return true;
}

void world_check(const SerializedPuzzle& puzzle, const StartingConfig& config, YieldFn yield) {
    State world{};
    world.puzzle = &puzzle;
    int N = puzzle.num_players;
    for (PlayerID pid = 0; pid < N; ++pid) {
        Player& p = world.players[pid];
        p.id = pid;
        p.claim = puzzle.player_claims[pid];
        p.character = make_ability(p.claim, 1);
        std::memset(p.protection_map, 0, sizeof(p.protection_map));
    }
    for (int i = 0; i < config.num_liars; ++i) {
        PlayerID pos = config.liar_positions[i];
        world.players[pos].character = make_ability(config.liar_characters[i], 1);
    }
    for (PlayerID pid = 0; pid < N; ++pid) {
        Player& p = world.players[pid];
        p.is_evil = is_category(p.character.type, CAT_MINION | CAT_DEMON);
        p.ever_behaved_evil = behaves_evil(world, pid);
        p.speculative_evil = (config.speculative_evil_mask & (1u << pid)) != 0;
        p.speculative_good = (config.speculative_good_mask & (1u << pid)) != 0;
        p.speculative_ceremad = (config.speculative_ceremad_mask & (1u << pid)) != 0;
    }

    if (!begin_game(world, puzzle.allow_duplicate_tokens_in_bag != 0)) {
        return;
    }

    SimSchedule sched = build_schedule(puzzle);
    run_schedule(world, sched, 0, config, yield);
}

void modify_category_counts(CharacterID type, int16_t bounds[4][2]) {
    switch (type) {
        case CHAR_Balloonist:
            bounds[0][0] -= 1;
            bounds[1][1] += 1;
            break;
        case CHAR_Baron:
            bounds[0][0] -= 2;
            bounds[0][1] -= 2;
            bounds[1][0] += 2;
            bounds[1][1] += 2;
            break;
        case CHAR_FangGu:
            bounds[0][0] -= 1;
            bounds[0][1] -= 1;
            bounds[1][0] += 1;
            bounds[1][1] += 1;
            break;
        case CHAR_Vigormortis:
            bounds[0][0] += 1;
            bounds[0][1] += 1;
            bounds[1][0] -= 1;
            bounds[1][1] -= 1;
            break;
        case CHAR_Marionette:
            bounds[0][1] += 1;
            bounds[1][0] -= 1;
            break;
        case CHAR_LordOfTyphon:
            bounds[0][0] = -99;
            bounds[0][1] = 99;
            bounds[1][0] = -99;
            bounds[1][1] = 99;
            bounds[2][0] += 1;
            bounds[2][1] += 1;
            break;
        case CHAR_Kazali:
        case CHAR_Xaan:
            bounds[0][0] = -99;
            bounds[0][1] = 99;
            bounds[1][0] = -99;
            bounds[1][1] = 99;
            break;
        default:
            break;
    }
}

bool check_token_counts(const SerializedPuzzle& puzzle, const CharacterID* in_play) {
    int N = puzzle.num_players;
    if (puzzle.player_zero_is_you) {
        bool in_hidden_self = false;
        for (int i = 0; i < puzzle.num_hidden_self; ++i) {
            if (puzzle.hidden_self[i] == in_play[0]) {
                in_hidden_self = true;
                break;
            }
        }
        if (!in_hidden_self && in_play[0] != puzzle.player_claims[0]) {
            return false;
        }
    }

    int16_t bounds[4][2] = {
        {puzzle.category_counts[0], puzzle.category_counts[0]},
        {puzzle.category_counts[1], puzzle.category_counts[1]},
        {puzzle.category_counts[2], puzzle.category_counts[2]},
        {puzzle.category_counts[3], puzzle.category_counts[3]},
    };
    int actual[4] = {0, 0, 0, 0};
    uint64_t seen_lo = 0, seen_hi = 0;

    for (int i = 0; i < N; ++i) {
        CharacterID c = in_play[i];
        modify_category_counts(c, bounds);
        Category cat = get_category(c);
        if (cat == CAT_TOWNSFOLK) actual[0]++;
        else if (cat == CAT_OUTSIDER) actual[1]++;
        else if (cat == CAT_MINION) actual[2]++;
        else if (cat == CAT_DEMON) actual[3]++;

        if (!puzzle.allow_duplicate_tokens_in_bag) {
            if (c < 64) {
                if (seen_lo & (1ULL << c)) return false;
                seen_lo |= (1ULL << c);
            } else {
                if (seen_hi & (1ULL << (c - 64))) return false;
                seen_hi |= (1ULL << (c - 64));
            }
        }
    }

    for (int k = 0; k < 4; ++k) {
        if (actual[k] < bounds[k][0] || actual[k] > bounds[k][1]) {
            return false;
        }
    }
    return true;
}

// Combinations generator helper
template <typename F>
void for_combinations(const CharacterID* arr, int n, int r, CharacterID* buf, int depth, int start, F&& callback) {
    if (depth == r) {
        callback(buf, r);
        return;
    }
    for (int i = start; i <= n - (r - depth); ++i) {
        buf[depth] = arr[i];
        for_combinations(arr, n, r, buf, depth + 1, i + 1, callback);
    }
}

template <typename F>
void for_combination_range(const CharacterID* arr, int n, int min_r, int max_r, F&& callback) {
    CharacterID buf[MAX_PLAYERS];
    for (int r = min_r; r <= max_r; ++r) {
        if (r < 0 || r > n) continue;
        for_combinations(arr, n, r, buf, 0, 0, callback);
    }
}

template <typename F>
void for_permutations(int n_players, int k, PlayerID* buf, uint16_t used_mask, int depth, F&& callback) {
    if (depth == k) {
        callback(buf, k);
        return;
    }
    for (PlayerID p = 0; p < n_players; ++p) {
        if (!(used_mask & (1u << p))) {
            buf[depth] = p;
            for_permutations(n_players, k, buf, used_mask | static_cast<uint16_t>(1u << p), depth + 1, callback);
        }
    }
}

} // namespace clockchecker

extern "C" {

int solve_puzzle_cpp(
    const clockchecker::SerializedPuzzle* puzzle_ptr,
    clockchecker::SerializedSolution* out_solutions,
    int max_solutions
) {
    using namespace clockchecker;
    const SerializedPuzzle& puzzle = *puzzle_ptr;
    const int N = puzzle.num_players;

    int num_solutions = 0;
    struct SolutionKey {
        CharacterID chars[MAX_PLAYERS * 2];
        bool operator==(const SolutionKey& o) const {
            return std::memcmp(chars, o.chars, sizeof(chars)) == 0;
        }
    };
    std::vector<SolutionKey> seen_keys;

    auto on_solution = [&](State& sol) {
        if (puzzle.deduplicate_initial_characters) {
            SolutionKey key{};
            for (int i = 0; i < N; ++i) {
                key.chars[i] = sol.initial_characters[i];
                key.chars[N + i] = sol.players[i].character.type;
            }
            for (const auto& k : seen_keys) {
                if (k == key) return;
            }
            seen_keys.push_back(key);
        }
        if (num_solutions < max_solutions) {
            SerializedSolution& out = out_solutions[num_solutions++];
            for (int i = 0; i < N; ++i) {
                const Player& p = sol.players[i];
                SerializedSolutionPlayer& sp = out.players[i];
                sp.initial_character = sol.initial_characters[i];
                sp.final_character = p.character.type;
                sp.drunklike_character = p.has_drunklike_char ? p.drunklike_char.type : CHAR_NONE;
                sp.is_evil = p.is_evil ? 1 : 0;
                sp.is_dead = p.is_dead ? 1 : 0;
                sp.droison_count = p.droison_count;
                sp.vigormortised = p.character.vigormortised ? 1 : 0;
                sp.self_droison = p.character.self_droison ? 1 : 0;
                sp.target = p.character.target;
                sp.aux_target = p.character.aux_target;
                sp.history_len = p.history_len;
                for (int h = 0; h < p.history_len && h < MAX_NIGHTS; ++h) {
                    sp.target_history[h] = p.target_history[h];
                }
            }
        }
    };
    YieldFn solution_yield = make_yield(on_solution);

    int num_minions = puzzle.category_counts[2];
    int num_demons = puzzle.category_counts[3];

    // Speculative lying characters (matching _speculative_lying_starting_characters)
    bool pithag_on_script = false;
    bool fanggu_on_script = false;
    bool snakecharmer_on_script = false;
    bool cerenovus_on_script = false;
    bool philo_on_script = false;
    for (int i = 0; i < puzzle.num_script; ++i) {
        CharacterID c = puzzle.script[i];
        if (c == CHAR_PitHag) pithag_on_script = true;
        if (c == CHAR_FangGu) fanggu_on_script = true;
        if (c == CHAR_SnakeCharmer) snakecharmer_on_script = true;
        if (c == CHAR_Cerenovus) cerenovus_on_script = true;
        if (c == CHAR_Philosopher) philo_on_script = true;
    }

    CharacterID evil_liars[MAX_SCRIPT];
    int num_evil_liars = 0;
    auto add_evil_liar = [&](CharacterID c) {
        for (int i = 0; i < num_evil_liars; ++i) {
            if (evil_liars[i] == c) return;
        }
        evil_liars[num_evil_liars++] = c;
    };

    bool has_outsiders_on_script = false;
    for (int i = 0; i < puzzle.num_script; ++i) {
        if (is_category(puzzle.script[i], CAT_OUTSIDER)) {
            has_outsiders_on_script = true;
            break;
        }
    }
    bool some_good_can_become_evil = snakecharmer_on_script || (fanggu_on_script && has_outsiders_on_script);
    if (pithag_on_script && some_good_can_become_evil) {
        for (int i = 0; i < puzzle.num_script; ++i) {
            if (!is_category(puzzle.script[i], CAT_MINION | CAT_DEMON)) {
                add_evil_liar(puzzle.script[i]);
            }
        }
    }
    int max_spec_evil = 0;
    if (fanggu_on_script) {
        max_spec_evil += 1;
        for (int i = 0; i < puzzle.num_script; ++i) {
            if (is_category(puzzle.script[i], CAT_OUTSIDER)) {
                add_evil_liar(puzzle.script[i]);
            }
        }
    }
    if (snakecharmer_on_script) {
        max_spec_evil += 1;
        add_evil_liar(CHAR_SnakeCharmer);
        if (philo_on_script) add_evil_liar(CHAR_Philosopher);
    }
    int max_spec_mad = cerenovus_on_script ? 1 : 0;

    int min_demons = std::max(0, num_demons - max_spec_mad - max_spec_evil);

    auto check_speculation = [&](const StartingConfig& cfg, const CharacterID* in_play) -> bool {
        if (puzzle.player_zero_is_you && ((cfg.speculative_evil_mask & 1) || (cfg.speculative_ceremad_mask & 1))) {
            return false;
        }
        bool pithag_in_play = false;
        bool fanggu_in_play = false;
        bool cerenovus_in_play = false;
        bool philo_in_play = false;
        bool sc_in_play = false;
        for (int i = 0; i < N; ++i) {
            if (in_play[i] == CHAR_PitHag) pithag_in_play = true;
            if (in_play[i] == CHAR_FangGu) fanggu_in_play = true;
            if (in_play[i] == CHAR_Cerenovus) cerenovus_in_play = true;
            if (in_play[i] == CHAR_Philosopher) philo_in_play = true;
            if (in_play[i] == CHAR_SnakeCharmer) sc_in_play = true;
        }
        bool cerenovus_possible = cerenovus_in_play || (pithag_in_play && cerenovus_on_script);
        if (cfg.speculative_ceremad_mask != 0 && !cerenovus_possible) {
            return false;
        }
        bool fanggu_possible = fanggu_in_play || (pithag_in_play && fanggu_on_script);
        bool anyone_becomes_outsider = pithag_in_play && has_outsiders_on_script;
        bool anyone_becomes_philo = pithag_in_play && philo_on_script;
        bool anyone_becomes_sc = snakecharmer_on_script && (pithag_in_play || anyone_becomes_philo);

        bool fanggu_used = false;
        for (PlayerID pid = 0; pid < N; ++pid) {
            if (!(cfg.speculative_evil_mask & (1u << pid))) continue;
            CharacterID character = in_play[pid];
            bool i_can_be_fanggu_jumped = fanggu_possible && !fanggu_used
                && (is_category(character, CAT_OUTSIDER) || anyone_becomes_outsider);
            bool i_can_be_sc = (character == CHAR_SnakeCharmer) || anyone_becomes_sc
                || (character == CHAR_Philosopher && snakecharmer_on_script);
            fanggu_used |= (i_can_be_fanggu_jumped && !i_can_be_sc);
            if (!i_can_be_fanggu_jumped && !i_can_be_sc) {
                return false;
            }
        }
        return true;
    };

    for_combination_range(puzzle.demons, puzzle.num_demons, min_demons, num_demons, [&](const CharacterID* demons, int n_d) {
        for_combination_range(puzzle.minions, puzzle.num_minions, num_minions, puzzle.num_minions, [&](const CharacterID* minions, int n_m) {
            for_combination_range(puzzle.hidden_good, puzzle.num_hidden_good, 0, puzzle.num_hidden_good, [&](const CharacterID* hgood, int n_hg) {
                for_combination_range(evil_liars, num_evil_liars, 0, max_spec_evil, [&](const CharacterID* spec_evil, int n_se) {
                    for_combination_range(puzzle.script, cerenovus_on_script ? puzzle.num_script : 0, 0, max_spec_mad, [&](const CharacterID* spec_mad, int n_sm) {
                        if (n_se + n_sm > puzzle.max_speculation) return;

                        int total_liars = n_d + n_m + n_hg + n_se + n_sm;
                        if (total_liars > N) return;

                        CharacterID liars[MAX_PLAYERS];
                        int idx = 0;
                        for (int i = 0; i < n_d; ++i) liars[idx++] = demons[i];
                        for (int i = 0; i < n_m; ++i) liars[idx++] = minions[i];
                        for (int i = 0; i < n_hg; ++i) liars[idx++] = hgood[i];
                        for (int i = 0; i < n_se; ++i) liars[idx++] = spec_evil[i];
                        for (int i = 0; i < n_sm; ++i) liars[idx++] = spec_mad[i];

                        PlayerID perm_buf[MAX_PLAYERS];
                        for_permutations(N, total_liars, perm_buf, 0, 0, [&](const PlayerID* liar_pos, int) {
                            CharacterID in_play[MAX_PLAYERS];
                            for (int i = 0; i < N; ++i) in_play[i] = puzzle.player_claims[i];
                            for (int i = 0; i < total_liars; ++i) in_play[liar_pos[i]] = liars[i];

                            if (!check_token_counts(puzzle, in_play)) return;

                            StartingConfig config{};
                            config.num_liars = static_cast<uint8_t>(total_liars);
                            for (int i = 0; i < total_liars; ++i) {
                                config.liar_characters[i] = liars[i];
                                config.liar_positions[i] = liar_pos[i];
                            }
                            for (int i = total_liars - n_se - n_sm; i < total_liars - n_sm; ++i) {
                                config.speculative_evil_mask |= static_cast<uint16_t>(1u << liar_pos[i]);
                            }
                            for (int i = total_liars - n_sm; i < total_liars; ++i) {
                                config.speculative_ceremad_mask |= static_cast<uint16_t>(1u << liar_pos[i]);
                            }

                            if (check_speculation(config, in_play)) {
                                world_check(puzzle, config, solution_yield);
                            }

                            int max_extra = std::min<int>(puzzle.max_speculation - (n_se + n_sm), 1);
                            if (max_extra > 0) {
                                bool pithag_in_play = false;
                                bool fanggu_in_play = false;
                                bool philo_in_play = false;
                                bool sc_in_play = false;
                                for (int i = 0; i < N; ++i) {
                                    if (in_play[i] == CHAR_PitHag) pithag_in_play = true;
                                    if (in_play[i] == CHAR_FangGu) fanggu_in_play = true;
                                    if (in_play[i] == CHAR_Philosopher) philo_in_play = true;
                                    if (in_play[i] == CHAR_SnakeCharmer) sc_in_play = true;
                                }
                                bool sc_possible = sc_in_play || (snakecharmer_on_script && (pithag_in_play || philo_in_play || (pithag_in_play && philo_on_script)));
                                bool anyone_becomes_outsider = pithag_in_play && has_outsiders_on_script;
                                bool fanggu_possible = fanggu_in_play || (pithag_in_play && fanggu_on_script);
                                bool anyone_becomes_sc = snakecharmer_on_script && pithag_in_play;
                                bool anyone_becomes_evil = (anyone_becomes_outsider && fanggu_possible) || anyone_becomes_sc;
                                if (sc_possible && anyone_becomes_evil) {
                                    for (int i = 0; i < total_liars - n_se - n_sm; ++i) {
                                        StartingConfig extra_cfg = config;
                                        extra_cfg.speculative_evil_mask |= static_cast<uint16_t>(1u << liar_pos[i]);
                                        if (check_speculation(extra_cfg, in_play)) {
                                            world_check(puzzle, extra_cfg, solution_yield);
                                        }
                                    }
                                }
                            }
                        });
                    });
                });
            });
        });
    });

    if (num_solutions == 0 && max_solutions > 0) {
        bool has_atheist = false;
        for (int i = 0; i < N; ++i) {
            if (puzzle.player_claims[i] == CHAR_Atheist) {
                has_atheist = true;
                break;
            }
        }
        if (has_atheist) {
            SerializedSolution& out = out_solutions[num_solutions++];
            for (int i = 0; i < N; ++i) {
                SerializedSolutionPlayer& sp = out.players[i];
                sp.initial_character = puzzle.player_claims[i];
                sp.final_character = puzzle.player_claims[i];
                sp.drunklike_character = CHAR_NONE;
                sp.is_evil = 0;
                sp.is_dead = 0;
                sp.droison_count = 0;
                sp.vigormortised = 0;
                sp.self_droison = 0;
                sp.target = NONE_PLAYER;
                sp.aux_target = NONE_PLAYER;
                sp.history_len = 0;
            }
        }
    }

    return num_solutions;
}

int get_serialized_puzzle_size() {
    return static_cast<int>(sizeof(clockchecker::SerializedPuzzle));
}

int get_serialized_solution_size() {
    return static_cast<int>(sizeof(clockchecker::SerializedSolution));
}

} // extern "C"
