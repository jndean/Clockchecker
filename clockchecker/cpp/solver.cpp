#include "clockchecker.hpp"
#include <algorithm>
#include <atomic>
#include <condition_variable>
#include <deque>
#include <mutex>
#include <thread>
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

thread_local const SerializedPuzzle* g_current_puzzle = nullptr;

inline bool hermit_has_outsider(CharacterID out_id) {
    if (g_current_puzzle == nullptr) return false;
    for (int i = 0; i < g_current_puzzle->num_hermit_outsiders; ++i) {
        if (g_current_puzzle->hermit_outsiders[i] == out_id) return true;
    }
    return false;
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
    ab.self_droison = (type == CHAR_Drunk || (type == CHAR_Hermit && hermit_has_outsider(CHAR_Drunk)));
    ab.target = NONE_PLAYER;
    ab.aux_target = NONE_PLAYER;
    ab.prev_category = 0;
    ab.prev_regs_mask = 0;
    ab.choice_night = -1;
    ab.aux_bool = false;
    ab.aux_mask = 0;
    ab.vig_poisoned_mask = 0;
    return ab;
}

inline Category get_category(CharacterID type) {
    return CHAR_META[type].category;
}

inline bool is_category(CharacterID type, uint8_t cat_mask) {
    return (CHAR_META[type].category & cat_mask) != 0;
}

// Starting configuration & schedule types (independent of MAX_P)
struct StartingConfig {
    uint8_t num_liars = 0;
    CharacterID liar_characters[MAX_PLAYERS];
    PlayerID liar_positions[MAX_PLAYERS];

    uint16_t speculative_evil_mask = 0;
    uint16_t speculative_good_mask = 0;
    uint16_t speculative_ceremad_mask = 0;
};

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

struct SolutionKey {
    CharacterID chars[MAX_PLAYERS * 2];
    bool operator==(const SolutionKey& o) const {
        return std::memcmp(chars, o.chars, sizeof(chars)) == 0;
    }
};

class WorkStealingPool {
public:
    using WorkerFn = void (*)(void*, int);

    static WorkStealingPool& get() {
        static WorkStealingPool instance;
        return instance;
    }

    int max_threads() const {
        return static_cast<int>(workers_.size()) + 1;
    }

    void run_job(void* ctx, WorkerFn fn, int num_workers) {
        std::lock_guard<std::mutex> run_lk(run_mtx_);
        int extra = num_workers - 1;
        if (extra > 0) {
            std::lock_guard<std::mutex> lk(job_mtx_);
            current_ctx_ = ctx;
            current_fn_ = fn;
            current_num_workers_ = num_workers;
            active_pool_workers_ = extra;
            ++job_gen_;
            job_cv_.notify_all();
        }

        fn(ctx, 0);

        if (extra > 0) {
            std::unique_lock<std::mutex> lk(job_mtx_);
            done_cv_.wait(lk, [&]() { return active_pool_workers_ == 0; });
            current_ctx_ = nullptr;
            current_fn_ = nullptr;
        }
    }

private:
    WorkStealingPool() {
        unsigned int hw = std::thread::hardware_concurrency();
        int n = (hw > 1) ? static_cast<int>(hw) : 1;
        workers_.reserve(n - 1);
        for (int tid = 1; tid < n; ++tid) {
            workers_.emplace_back([this, tid]() { worker_loop(tid); });
        }
    }

    ~WorkStealingPool() {
        {
            std::lock_guard<std::mutex> lk(job_mtx_);
            shutdown_ = true;
            job_cv_.notify_all();
        }
        for (auto& t : workers_) {
            if (t.joinable()) t.join();
        }
    }

    void worker_loop(int tid) {
        uint64_t my_gen = 0;
        while (true) {
            void* ctx = nullptr;
            WorkerFn fn = nullptr;
            {
                std::unique_lock<std::mutex> lk(job_mtx_);
                job_cv_.wait(lk, [&]() {
                    return shutdown_ || (job_gen_ != my_gen && current_ctx_ != nullptr && tid < current_num_workers_);
                });
                if (shutdown_) return;
                my_gen = job_gen_;
                ctx = current_ctx_;
                fn = current_fn_;
            }
            fn(ctx, tid);
            {
                std::lock_guard<std::mutex> lk(job_mtx_);
                if (--active_pool_workers_ == 0) {
                    done_cv_.notify_one();
                }
            }
        }
    }

    std::mutex run_mtx_;
    std::mutex job_mtx_;
    std::condition_variable job_cv_;
    std::condition_variable done_cv_;
    void* current_ctx_ = nullptr;
    WorkerFn current_fn_ = nullptr;
    int current_num_workers_ = 0;
    uint64_t job_gen_ = 0;
    int active_pool_workers_ = 0;
    bool shutdown_ = false;
    std::vector<std::thread> workers_;
};

template <int MAX_P>
struct SolverEngine {
    using Player = PlayerT<MAX_P>;
    using State = StateT<MAX_P>;

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
static inline YieldFn make_yield(F& lambda) {
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

inline AbilityInstance* get_ability(Player& p, CharacterID type) {
    if (type == CHAR_NONE || p.character.type == type) {
        return &p.character;
    }
    if (p.character.type == CHAR_Philosopher && p.has_philo_ability && p.philo_ability.type == type) {
        return &p.philo_ability;
    }
    if (p.character.type == CHAR_Hermit && hermit_has_outsider(type)) {
        return &p.character;
    }
    if (p.has_boffin_ability && p.boffin_ability.type == type) {
        return &p.boffin_ability;
    }
    return nullptr;
}

inline const AbilityInstance* get_ability(const Player& p, CharacterID type) {
    if (type == CHAR_NONE || p.character.type == type) {
        return &p.character;
    }
    if (p.character.type == CHAR_Philosopher && p.has_philo_ability && p.philo_ability.type == type) {
        return &p.philo_ability;
    }
    if (p.character.type == CHAR_Hermit && hermit_has_outsider(type)) {
        return &p.character;
    }
    if (p.has_boffin_ability && p.boffin_ability.type == type) {
        return &p.boffin_ability;
    }
    return nullptr;
}

inline bool has_ability(const Player& p, CharacterID type) {
    return get_ability(p, type) != nullptr;
}

inline bool ability_acts_like(const Player& p, CharacterID type) {
    if (get_ability(p, type) != nullptr) return true;
    if (p.has_drunklike_char && p.drunklike_char.type == type) return true;
    return false;
}

inline AbilityInstance* get_ability_that_acts_like(Player& p, CharacterID type) {
    if (AbilityInstance* ab = get_ability(p, type)) return ab;
    if (p.has_drunklike_char && p.drunklike_char.type == type) return &p.character;
    return nullptr;
}

inline AbilityInstance& get_ability_ref(State& state, PlayerID pid, CharacterID which_ability = CHAR_NONE) {
    Player& p = state.players[pid];
    if (which_ability != CHAR_NONE) {
        if (AbilityInstance* ab = get_ability_that_acts_like(p, which_ability)) {
            return *ab;
        }
    }
    return p.character;
}

inline bool is_droisoned(const State& state, const AbilityInstance& ab, PlayerID me) {
    PlayerID pid = (ab.ability_src != NONE_PLAYER) ? ab.ability_src : me;
    return state.players[pid].droison_count > 0;
}

inline uint8_t get_misreg_categories(const State&, const Player& p, bool assume_droisoned = false) {
    uint8_t cats = 0;
    if (!(p.droison_count > 0 || assume_droisoned)) {
        cats |= CHAR_META[p.character.type].misregister_categories;
        if (p.character.type == CHAR_Philosopher && p.has_philo_ability) {
            cats |= CHAR_META[p.philo_ability.type].misregister_categories;
        }
        if (p.character.type == CHAR_Hermit && g_current_puzzle != nullptr) {
            for (int i = 0; i < g_current_puzzle->num_hermit_outsiders; ++i) {
                cats |= (CHAR_META[g_current_puzzle->hermit_outsiders[i]].misregister_categories & ~CAT_OUTSIDER);
            }
        }
    }
    if (p.has_boffin_ability) {
        cats |= CHAR_META[p.boffin_ability.type].misregister_categories;
    }
    return cats;
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
    if (CHAR_META[type].is_drunklike) return true;
    if (type == CHAR_Hermit && g_current_puzzle != nullptr) {
        for (int i = 0; i < g_current_puzzle->num_hermit_outsiders; ++i) {
            if (CHAR_META[g_current_puzzle->hermit_outsiders[i]].is_drunklike) return true;
        }
    }
    return false;
}

inline bool char_lies_about_character_and_info(const Player& p) {
    if (CHAR_META[p.character.type].lies_about_character_and_info) return true;
    if (p.character.type == CHAR_Philosopher && p.has_philo_ability
        && CHAR_META[p.philo_ability.type].lies_about_character_and_info) {
        return true;
    }
    if (p.character.type == CHAR_Hermit && g_current_puzzle != nullptr) {
        for (int i = 0; i < g_current_puzzle->num_hermit_outsiders; ++i) {
            if (CHAR_META[g_current_puzzle->hermit_outsiders[i]].lies_about_character_and_info) return true;
        }
    }
    return false;
}

inline bool lies_about_character(const State& state, PlayerID pid, bool ignore_own_ability = false) {
    const Player& p = state.players[pid];
    if (pid == 0 && state.puzzle->player_zero_is_you) {
        return draws_wrong_token(p.character.type);
    }
    return behaves_evil(state, pid)
        || (char_lies_about_character_and_info(p) && !ignore_own_ability)
        || p.speculative_ceremad;
}

inline bool lies_about_info(const State& state, PlayerID pid) {
    const Player& p = state.players[pid];
    if (pid == 0 && state.puzzle->player_zero_is_you) {
        return draws_wrong_token(p.character.type);
    }
    return behaves_evil(state, pid)
        || char_lies_about_character_and_info(p)
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

inline void droison_player(State& state, PlayerID target, PlayerID) {
    Player& p = state.players[target];
    p.droison_count += 1;
    maybe_deactivate_effects(state, p.character, target, REASON_DROISON);
}

inline void undroison_player(State& state, PlayerID target, PlayerID) {
    Player& p = state.players[target];
    p.droison_count -= 1;
    maybe_activate_effects(state, p.character, target, REASON_DROISON);
}

// Core Info evaluation helpers
inline STBool eval_is_evil(const State& state, PlayerID target, PlayerID = NONE_PLAYER) {
    const Player& p = state.players[target];
    if (const AbilityInstance* recluse = get_ability(p, CHAR_Recluse)) {
        if (!is_droisoned(state, *recluse, target)) {
            return p.is_evil ? STBoolVal::TRUE : STBoolVal::FALSE_MAYBE;
        }
    }
    if (const AbilityInstance* spy = get_ability(p, CHAR_Spy)) {
        if (!is_droisoned(state, *spy, target)) {
            return p.is_evil ? STBoolVal::TRUE_MAYBE : STBoolVal::FALSE;
        }
    }
    return STBool(p.is_evil);
}

inline STBool eval_is_alive(const State& state, PlayerID target, PlayerID = NONE_PLAYER) {
    const Player& p = state.players[target];
    if (p.is_dead) return STBoolVal::FALSE;
    if (p.character.type == CHAR_Zombuul && p.character.aux_bool) {
        return STBoolVal::FALSE_LYING;
    }
    return STBoolVal::TRUE;
}

inline STBool eval_is_character(const State& state, PlayerID target, CharacterID char_id, PlayerID = NONE_PLAYER) {
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
    PlayerID = NONE_PLAYER
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
    if (ab.type == CHAR_Philosopher) {
        if (player.has_philo_ability) {
            return wakes_tonight_ability(state, player.philo_ability, me);
        }
        if (ab.aux_bool) {
            return player.has_drunklike_char && wakes_tonight_ability(state, player.drunklike_char, me);
        }
    }
    if (ab.type == CHAR_Hermit) {
        if (player.has_drunklike_char && wakes_tonight_ability(state, player.drunklike_char, me)) {
            return true;
        }
        if (g_current_puzzle != nullptr) {
            for (int i = 0; i < g_current_puzzle->num_hermit_outsiders; ++i) {
                CharacterID out_id = g_current_puzzle->hermit_outsiders[i];
                if (!CHAR_META[out_id].is_drunklike) {
                    AbilityInstance tmp = ab;
                    tmp.type = out_id;
                    if (wakes_tonight_ability(state, tmp, me)) return true;
                }
            }
        }
        return false;
    }
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
                    if (ch.type == CHAR_Philosopher) {
                        const Player& pl = state.players[node.player1];
                        return STBool(pl.has_philo_ability && pl.philo_ability.has_spent_attr
                                      && pl.philo_ability.spent == (node.flag != 0));
                    }
                    return STBool(ch.has_spent_attr && ch.spent == (node.flag != 0));
                default:
                    return STBoolVal::FALSE;
            }
        }
        case INFO_WIDOW_POISONED: {
            const Player& target = state.players[node.player1];
            if (target.droison_count <= 0) {
                return STBoolVal::FALSE;
            }
            for (PlayerID pid = 0; pid < N; ++pid) {
                const Player& p = state.players[pid];
                if (!p.is_dead && p.droison_count == 0) {
                    const AbilityInstance* w = get_ability(p, CHAR_Widow);
                    if (w != nullptr && w->target == node.player1) {
                        return STBoolVal::TRUE;
                    }
                }
            }
            return STBoolVal::FALSE;
        }
        case INFO_PLAYER_ATTR_EQ: {
            const Player& pl = state.players[node.player1];
            switch (static_cast<AttrID>(node.category)) {
                case ATTR_CEREMAD:
                    return STBool(pl.ceremad > 0 && pl.ceremad == node.count);
                case ATTR_IS_EVIL:
                    return STBool(static_cast<int>(pl.is_evil) == node.count);
                case ATTR_IS_DEAD:
                    return STBool(static_cast<int>(pl.is_dead) == node.count);
                case ATTR_DROISON_COUNT:
                    return STBool(pl.droison_count == node.count);
                case ATTR_WOKE_TONIGHT:
                    return STBool(static_cast<int>(pl.woke_tonight) == node.count);
                case ATTR_SAFE_FROM_DEMON_COUNT:
                    return STBool(pl.safe_from_demon_count > 0 && pl.safe_from_demon_count == node.count);
                case ATTR_SAFE_FROM_EXECUTION:
                    return STBool(pl.safe_from_execution > 0 && pl.safe_from_execution == node.count);
                case ATTR_EXORCISED_COUNT:
                    return STBool(pl.exorcised_count > 0 && pl.exorcised_count == node.count);
                default:
                    return STBoolVal::FALSE;
            }
        }
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

        case INFO_CHARACTER_TYPES_AMONG_PLAYERS: {
            int count = 0;
            constexpr uint8_t ALL_CATS[5] = {CAT_TOWNSFOLK, CAT_OUTSIDER, CAT_MINION, CAT_DEMON, CAT_TRAVELLER};
            for (int c = 0; c < 5; ++c) {
                bool any_of_cat = false;
                for (int i = 0; i < node.extra_count; ++i) {
                    PlayerID pid = static_cast<PlayerID>(node.extra_indices[i]);
                    if (eval_is_category(state, pid, ALL_CATS[c], false, src).not_false()) {
                        any_of_cat = true;
                        break;
                    }
                }
                if (any_of_cat) count += 1;
            }
            return STBool(count == node.count);
        }

        case INFO_CHARACTER_IS_NEXT_TO_CHARACTER: {
            STBool result = STBoolVal::FALSE;
            for (PlayerID p = 0; p < N; ++p) {
                STBool is_char1 = eval_is_character(state, p, node.character1, src);
                if (is_char1.is_false()) continue;
                PlayerID left = static_cast<PlayerID>((p - 1 + N) % N);
                PlayerID right = static_cast<PlayerID>((p + 1) % N);
                STBool neighbours_char2 = eval_is_character(state, left, node.character1, src)
                                        | eval_is_character(state, right, node.character1, src);
                result |= (is_char1 & neighbours_char2);
            }
            return result;
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

        case PING_PRODIGY: {
            STBool chose_evil = eval_is_evil(state, node.player1, src);
            STBool shown_evil = eval_is_evil(state, node.player2, src);
            const AbilityInstance* pr = get_ability(state.players[src], CHAR_Progidy);
            if (pr != nullptr && pr->choice_night == 1) {
                return chose_evil == shown_evil;
            }
            return chose_evil ^ shown_evil;
        }

        case PING_FLOWERGIRL:
        case PING_TOWN_CRIER: {
            const Player& p = state.players[src];
            return STBool(node.flag != 0) == p.saved_day_bool;
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
    CharacterID lookup_type = (ab.type == CHAR_Hermit) ? state.currently_acting_character : ab.type;
    int16_t ping_idx = -1;
    if (state.current_phase == PHASE_NIGHT) {
        ping_idx = get_night_info(state, lookup_type, me, state.night);
    } else if (state.current_phase == PHASE_DAY) {
        ping_idx = get_day_info(state, lookup_type, me);
    }

    Player& player = state.players[me];
    if (ping_idx == -1 || lies_about_info(state, me)) {
        return true;
    }
    if (player.is_dead && !even_if_dead) {
        return false;
    }
    bool has_spent = (ab.type == CHAR_Hermit) ? CHAR_META[lookup_type].has_spent : ab.has_spent_attr;
    if (has_spent) {
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
        case CHAR_Cerenovus:
            if (ab.target != NONE_PLAYER) {
                state.players[ab.target].ceremad += 1;
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
        case CHAR_Widow:
            if (ab.target == me) {
                state.players[me].droison_count += 1;
            } else if (ab.target != NONE_PLAYER) {
                droison_player(state, ab.target, me);
                if (state.widow_pinged_night == -1) {
                    state.widow_pinged_night = (state.night != 0)
                        ? state.night
                        : static_cast<int8_t>(state.day + 1);
                }
            }
            break;
        case CHAR_Exorcist:
            if (ab.target != NONE_PLAYER) {
                state.players[ab.target].exorcised_count += 1;
            }
            break;
        case CHAR_DevilsAdvocate:
            if (ab.target != NONE_PLAYER) {
                state.players[ab.target].safe_from_execution += 1;
            }
            break;
        case CHAR_Riot:
            if (state.day == 3 && !state.players[me].is_dead && state.players[me].exorcised_count == 0) {
                state.rioting_count += 1;
                ab.aux_bool = true;
            }
            break;
        case CHAR_Vigormortis:
            for (PlayerID pid = 0; pid < state.puzzle->num_players; ++pid) {
                if (ab.vig_poisoned_mask & (1u << pid)) {
                    droison_player(state, pid, me);
                }
                if (ab.aux_mask & (1u << pid)) {
                    state.players[pid].character.vigormortised = true;
                }
            }
            break;
        case CHAR_Philosopher:
            if (ab.self_droison) {
                state.players[me].droison_count += 1;
                break;
            }
            if (!state.players[me].has_philo_ability) {
                break;
            }
            if (ab.target != NONE_PLAYER) {
                droison_player(state, ab.target, me);
            }
            maybe_activate_effects(state, state.players[me].philo_ability, me);
            break;
        case CHAR_Boffin:
            if (ab.target != NONE_PLAYER) {
                Player& demon = state.players[ab.target];
                demon.boffin_ability = state.players[me].inactive_boffin_ability;
                demon.has_boffin_ability = true;
                state.players[me].inactive_boffin_ability.type = CHAR_NONE;
                update_character_callbacks(state);
                maybe_activate_effects(state, demon.boffin_ability, ab.target);
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
        case CHAR_Cerenovus:
            if (ab.target != NONE_PLAYER) {
                state.players[ab.target].ceremad -= 1;
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
        case CHAR_Widow:
            if (ab.target == me) {
                state.players[me].droison_count -= 1;
            } else if (ab.target != NONE_PLAYER) {
                undroison_player(state, ab.target, me);
            }
            break;
        case CHAR_Exorcist:
            if (ab.target != NONE_PLAYER) {
                state.players[ab.target].exorcised_count -= 1;
            }
            break;
        case CHAR_DevilsAdvocate:
            if (ab.target != NONE_PLAYER) {
                state.players[ab.target].safe_from_execution -= 1;
            }
            break;
        case CHAR_Riot:
            if (ab.aux_bool) {
                ab.aux_bool = false;
                state.rioting_count -= 1;
            }
            break;
        case CHAR_Vigormortis:
            for (PlayerID pid = 0; pid < state.puzzle->num_players; ++pid) {
                if (ab.vig_poisoned_mask & (1u << pid)) {
                    undroison_player(state, pid, me);
                }
                if (ab.aux_mask & (1u << pid)) {
                    state.players[pid].character.vigormortised = false;
                }
            }
            break;
        case CHAR_Philosopher:
            if (ab.self_droison) {
                undroison_player(state, me, me);
                break;
            }
            if (!state.players[me].has_philo_ability) {
                break;
            }
            if (ab.target != NONE_PLAYER) {
                undroison_player(state, ab.target, me);
            }
            maybe_deactivate_effects(state, state.players[me].philo_ability, me);
            break;
        case CHAR_Boffin:
            if (ab.target != NONE_PLAYER) {
                Player& demon = state.players[ab.target];
                maybe_deactivate_effects(state, demon.boffin_ability, ab.target);
                state.players[me].inactive_boffin_ability = demon.boffin_ability;
                demon.has_boffin_ability = false;
                demon.boffin_ability.type = CHAR_NONE;
                update_character_callbacks(state);
            }
            break;
        default:
            break;
    }
}

void maybe_activate_effects(State& state, AbilityInstance& ab, PlayerID me, Reason reason = REASON_NONE) {
    if (ab.type == CHAR_Puzzlemaster) {
        if (!ab.effects_active && !is_droisoned(state, ab, me) && reason != REASON_RESURRECTION) {
            ab.effects_active = true;
            droison_player(state, ab.target, me);
        }
        return;
    }
    if (ab.type == CHAR_Sweetheart) {
        if (!ab.effects_active && !is_droisoned(state, ab, me) && ab.target != NONE_PLAYER && reason != REASON_RESURRECTION) {
            ab.effects_active = true;
            droison_player(state, ab.target, me);
        }
        return;
    }
    if (ab.type == CHAR_Hermit) {
        if (hermit_has_outsider(CHAR_Puzzlemaster)) {
            if (!ab.effects_active && !is_droisoned(state, ab, me) && ab.target != NONE_PLAYER && reason != REASON_RESURRECTION) {
                ab.effects_active = true;
                droison_player(state, ab.target, me);
            }
        }
        if (hermit_has_outsider(CHAR_Sweetheart)) {
            if (!(ab.aux_mask & 1u) && !is_droisoned(state, ab, me) && ab.aux_target != NONE_PLAYER && reason != REASON_RESURRECTION) {
                ab.aux_mask |= 1u;
                droison_player(state, ab.aux_target, me);
            }
        }
        return;
    }
    Player& player = state.players[me];
    if (!ab.effects_active && !is_droisoned(state, ab, me) && (!player.is_dead || ab.vigormortised)) {
        ab.effects_active = true;
        activate_effects_impl(state, ab, me);
    }
}

void maybe_deactivate_effects(State& state, AbilityInstance& ab, PlayerID me, Reason reason = REASON_NONE) {
    if (ab.type == CHAR_Puzzlemaster || ab.type == CHAR_Sweetheart) {
        if (ab.effects_active && reason != REASON_DEATH && ab.target != me) {
            ab.effects_active = false;
            undroison_player(state, ab.target, me);
        }
        return;
    }
    if (ab.type == CHAR_Hermit) {
        if (hermit_has_outsider(CHAR_Puzzlemaster)) {
            if (ab.effects_active && reason != REASON_DEATH && ab.target != me && ab.target != NONE_PLAYER) {
                ab.effects_active = false;
                undroison_player(state, ab.target, me);
            }
        }
        if (hermit_has_outsider(CHAR_Sweetheart)) {
            if ((ab.aux_mask & 1u) && reason != REASON_DEATH && ab.aux_target != me && ab.aux_target != NONE_PLAYER) {
                ab.aux_mask &= ~static_cast<uint16_t>(1u);
                undroison_player(state, ab.aux_target, me);
            }
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
        const Player& p = state.players[pid];
        uint8_t mask = CHAR_META[p.character.type].callbacks_mask;
        if (p.character.type == CHAR_Philosopher && p.has_philo_ability) {
            mask |= CHAR_META[p.philo_ability.type].callbacks_mask;
        }
        if (p.has_boffin_ability) {
            mask |= CHAR_META[p.boffin_ability.type].callbacks_mask;
        }
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

void base_apply_death(State& state, PlayerID me, PlayerID src, YieldFn yield) {
    if (AbilityInstance* rk = get_ability(state.players[me], CHAR_Ravenkeeper)) {
        if (state.night != 0) {
            rk->choice_night = state.night;
            rk->aux_bool = is_droisoned(state, *rk, me);
            state.players[me].woke_tonight = true;
        }
    } else if (AbilityInstance* sage = get_ability(state.players[me], CHAR_Sage)) {
        STBool killed_by_demon = (src != NONE_PLAYER)
            ? eval_is_category(state, src, CAT_DEMON, false, me)
            : STBoolVal::FALSE;
        if (state.night != 0 && killed_by_demon.not_false()) {
            sage->choice_night = state.night;
            sage->aux_bool = is_droisoned(state, *sage, me);
            state.players[me].woke_tonight = true;
        }
    }

    auto after_pre_death = [&](State& substate) {
        Player& player = substate.players[me];
        player.is_dead = true;
        maybe_deactivate_effects(substate, player.character, me, REASON_DEATH);
        if (has_ability(player, CHAR_Mutant)) {
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

void apply_death(State& state, PlayerID me, PlayerID src, YieldFn yield) {
    if (AbilityInstance* sh = get_ability(state.players[me], CHAR_Sweetheart)) {
        if (!is_droisoned(state, *sh, me)) {
            int N = state.puzzle->num_players;
            for (PlayerID pid = 0; pid < N; ++pid) {
                State new_state = state;
                AbilityInstance* new_sh = get_ability(new_state.players[me], CHAR_Sweetheart);
                if (new_sh->type == CHAR_Hermit) {
                    new_sh->aux_target = pid;
                } else {
                    new_sh->target = pid;
                }
                maybe_activate_effects(new_state, *new_sh, me, REASON_DEATH);
                base_apply_death(new_state, me, src, yield);
            }
            return;
        }
    }
    base_apply_death(state, me, src, yield);
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
    if (AbilityInstance* saint = get_ability(player, CHAR_Saint)) {
        bool droisoned = is_droisoned(state, *saint, me);
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
    if (state.num_char_changes < MAX_CHAR_CHANGES) {
        uint8_t rnd = (state.current_phase == PHASE_NIGHT) ? static_cast<uint8_t>(state.night)
                    : (state.current_phase == PHASE_DAY)   ? static_cast<uint8_t>(state.day)
                                                           : 0;
        state.char_changes[state.num_char_changes++] = CharChangeEntry{
            pid,
            player.character.type,
            static_cast<uint8_t>((static_cast<uint8_t>(state.current_phase) << 6) | (rnd & 0x3Fu))
        };
    }
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
    player.has_philo_ability = false;
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

void widow_run_first_night(State& state, AbilityInstance& ab, PlayerID me, YieldFn yield) {
    Player& player = state.players[me];
    int N = state.puzzle->num_players;
    uint8_t ext_count = state.puzzle->external_info_count[state.night][CHAR_Widow];
    const ExternalInfoEntry* ext_entries = state.puzzle->external_info[state.night][CHAR_Widow];

    if (player.is_dead) {
        return;
    }
    if (is_droisoned(state, ab, me)) {
        for (uint8_t i = 0; i < ext_count; ++i) {
            if (!behaves_evil(state, ext_entries[i].player_id)) {
                return;
            }
        }
        math_misregistration(state, me);
        yield(state);
        return;
    }

    PlayerID ping_receivers[MAX_PLAYERS];
    int n_receivers = 0;
    uint16_t receiver_mask = 0;
    for (uint8_t i = 0; i < ext_count; ++i) {
        PlayerID pid = ext_entries[i].player_id;
        if (!(receiver_mask & (1u << pid))) {
            receiver_mask |= static_cast<uint16_t>(1u << pid);
            ping_receivers[n_receivers++] = pid;
        }
    }

    int count_non_evil_receivers = 0;
    for (int i = 0; i < n_receivers; ++i) {
        if (!behaves_evil(state, ping_receivers[i])) {
            count_non_evil_receivers += 1;
        }
    }
    if (count_non_evil_receivers > 1) {
        return;
    }

    PlayerID valid_ping_targets[MAX_PLAYERS];
    int n_valid_ping_targets = 0;
    if (n_receivers == 0) {
        for (PlayerID pid = 0; pid < N; ++pid) {
            if (behaves_evil(state, pid)) {
                valid_ping_targets[n_valid_ping_targets++] = pid;
            }
        }
        valid_ping_targets[n_valid_ping_targets++] = NONE_PLAYER;
    } else {
        for (int i = 0; i < n_receivers; ++i) {
            valid_ping_targets[n_valid_ping_targets++] = ping_receivers[i];
        }
    }

    CharacterID ab_type = ab.type;
    for (PlayerID poison_target = 0; poison_target < N; ++poison_target) {
        State poison_state = state;
        AbilityInstance& new_widow = get_ability_ref(poison_state, me, ab_type);
        new_widow.target = poison_target;
        maybe_activate_effects(poison_state, new_widow, me);

        PlayerID real_good_players[MAX_PLAYERS];
        int n_real_good = 0;
        for (PlayerID pid = 0; pid < N; ++pid) {
            if (!poison_state.players[pid].is_evil) {
                real_good_players[n_real_good++] = pid;
            }
        }
        if (n_real_good > 0 && n_receivers == 0 && !is_droisoned(poison_state, new_widow, me)) {
            bool any_good_behaves_evil = false;
            for (int i = 0; i < n_real_good; ++i) {
                if (behaves_evil(poison_state, real_good_players[i])) {
                    any_good_behaves_evil = true;
                    break;
                }
            }
            if (!any_good_behaves_evil) {
                bool can_suppress_all_good = true;
                for (int i = 0; i < n_real_good; ++i) {
                    if (eval_is_evil(poison_state, real_good_players[i], me).is_false()) {
                        can_suppress_all_good = false;
                        break;
                    }
                }
                if (can_suppress_all_good) {
                    math_misregistration(poison_state, me);
                    yield(poison_state);
                }
                continue;
            }
        }

        bool yielded_no_ping_world = false;
        for (int ti = 0; ti < n_valid_ping_targets; ++ti) {
            PlayerID ping_target = valid_ping_targets[ti];
            if (is_droisoned(poison_state, new_widow, me)) {
                if (ping_target != NONE_PLAYER && !behaves_evil(poison_state, ping_target)) {
                    continue;
                }
                if (!yielded_no_ping_world) {
                    yielded_no_ping_world = true;
                    State new_state = poison_state;
                    if (n_real_good > 0) {
                        math_misregistration(new_state, me);
                    }
                    yield(new_state);
                }
            } else if (ping_target == NONE_PLAYER) {
                if (n_real_good == 0 && !yielded_no_ping_world) {
                    yielded_no_ping_world = true;
                    State new_state = poison_state;
                    yield(new_state);
                }
            } else {
                STBool is_good = ~eval_is_evil(poison_state, ping_target, me);
                if (is_good.not_false()) {
                    State new_state = poison_state;
                    math_misregistration(new_state, me, &is_good);
                    yield(new_state);
                }
            }
        }
    }
}

void philo_choose_ability(State& state, PlayerID me, CharacterID char_t, YieldFn yield) {
    Player& philo = state.players[me];
    if (is_droisoned(state, philo.character, me)) {
        philo.drunklike_char = make_ability(char_t, state.night);
        philo.has_drunklike_char = true;
        philo.character.aux_bool = true;
        philo.character.target = NONE_PLAYER;
        math_misregistration(state, me);
        yield(state);
        return;
    }

    philo.philo_ability = make_ability(char_t, state.night);
    philo.has_philo_ability = true;
    update_character_callbacks(state);

    auto after_sub_setup = [&](State& substate) {
        int N = substate.puzzle->num_players;
        PlayerID drunk_targets[MAX_PLAYERS];
        int n_targets = 0;
        for (PlayerID pid = 0; pid < N; ++pid) {
            if (eval_is_character(substate, pid, char_t, me).not_false()) {
                drunk_targets[n_targets++] = pid;
            }
        }
        if (n_targets == 0) {
            drunk_targets[n_targets++] = NONE_PLAYER;
        }
        for (int i = 0; i < n_targets; ++i) {
            State new_state = substate;
            AbilityInstance& new_philo = new_state.players[me].character;
            new_philo.target = drunk_targets[i];
            maybe_activate_effects(new_state, new_philo, me);
            yield(new_state);
        }
    };
    run_character_setup(state, me, make_yield(after_sub_setup), char_t);
}

void run_character_setup(State& state, PlayerID me, YieldFn yield, CharacterID which_ability = CHAR_NONE) {
    Player& player = state.players[me];
    AbilityInstance& ab = get_ability_ref(state, me, which_ability);
    CharacterID ab_type = ab.type;
    int N = state.puzzle->num_players;

    switch (ab_type) {
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

        case CHAR_Hermit: {
            int n_outs = state.puzzle->num_hermit_outsiders;
            auto step = [&](State& s, int idx, YieldFn y) {
                CharacterID out_id = s.puzzle->hermit_outsiders[idx];
                Player& sp = s.players[me];
                AbilityInstance& sab = get_ability_ref(s, me, ab_type);
                if (out_id == CHAR_Drunk) {
                    if (!is_category(sp.claim, CAT_TOWNSFOLK)) {
                        return;
                    }
                    sp.drunklike_char = make_ability(sp.claim, sab.first_night);
                    sp.has_drunklike_char = true;
                    drunklike_run_simulation(s, me, y);
                } else if (out_id == CHAR_Lunatic) {
                    for (int di = 0; di < s.puzzle->num_demons; ++di) {
                        State substate = s;
                        Player& subp = substate.players[me];
                        subp.drunklike_char = make_ability(s.puzzle->demons[di], sab.first_night);
                        subp.has_drunklike_char = true;
                        drunklike_run_simulation(substate, me, y);
                    }
                } else if (out_id == CHAR_Puzzlemaster) {
                    for (PlayerID pid = 0; pid < N; ++pid) {
                        State new_state = s;
                        AbilityInstance& pm = get_ability_ref(new_state, me, ab_type);
                        pm.target = pid;
                        maybe_activate_effects(new_state, pm, me, REASON_SETUP);
                        y(new_state);
                    }
                } else {
                    y(s);
                }
            };
            apply_seq(state, 0, n_outs, step, yield);
            return;
        }

        case CHAR_Boffin: {
            PlayerID demon_ids[MAX_PLAYERS];
            int n_demons = 0;
            for (PlayerID pid = 0; pid < N; ++pid) {
                if (eval_is_category(state, pid, CAT_DEMON, false, me).not_false()) {
                    demon_ids[n_demons++] = pid;
                }
            }
            CharacterID abilities[MAX_SCRIPT];
            int n_abilities = 0;
            for (int i = 0; i < state.puzzle->num_script; ++i) {
                CharacterID c = state.puzzle->script[i];
                if (is_category(c, CAT_TOWNSFOLK | CAT_OUTSIDER)
                    && c != CHAR_Drunk && c != CHAR_Politician
                    && eval_is_in_play(state, c, me).not_true()) {
                    abilities[n_abilities++] = c;
                }
            }
            uint8_t next_night = (state.night != 0) ? state.night
                               : (state.day != 0)   ? static_cast<uint8_t>(state.day + 1)
                                                    : static_cast<uint8_t>(1);
            for (int di = 0; di < n_demons; ++di) {
                PlayerID demon_id = demon_ids[di];
                for (int ai = 0; ai < n_abilities; ++ai) {
                    CharacterID ability_t = abilities[ai];
                    State new_state = state;
                    AbilityInstance& new_boffin = get_ability_ref(new_state, me, ab_type);
                    new_boffin.target = demon_id;
                    new_boffin.effects_active = true;
                    Player& demon = new_state.players[demon_id];
                    demon.boffin_ability = make_ability(ability_t, next_night);
                    demon.boffin_ability.ability_src = me;
                    demon.has_boffin_ability = true;
                    update_character_callbacks(new_state);
                    run_character_setup(new_state, demon_id, yield, ability_t);
                }
            }
            return;
        }

        case CHAR_Progidy: {
            if (ab.choice_night != -1) {
                yield(state);
                return;
            }
            PlayerID other_prodigies[MAX_PLAYERS];
            int n_others = 0;
            for (PlayerID pid = 0; pid < N; ++pid) {
                if (pid != me && has_ability(state.players[pid], CHAR_Progidy)) {
                    other_prodigies[n_others++] = pid;
                }
            }
            if (n_others > 1) {
                return;
            }
            // I am Solar
            State solar_state = state;
            if (AbilityInstance* my_p = get_ability(solar_state.players[me], CHAR_Progidy)) {
                my_p->choice_night = 1;
            }
            if (n_others == 1) {
                if (AbilityInstance* oth_p = get_ability(solar_state.players[other_prodigies[0]], CHAR_Progidy)) {
                    oth_p->choice_night = 0;
                }
            }
            yield(solar_state);

            // I am Lunar
            ab.choice_night = 0;
            if (n_others == 1) {
                if (AbilityInstance* oth_p = get_ability(state.players[other_prodigies[0]], CHAR_Progidy)) {
                    oth_p->choice_night = 1;
                }
            }
            yield(state);
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
                    get_ability_ref(new_state, me, ab_type).target = pid;
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
                    AbilityInstance& new_nd = get_ability_ref(new_state, me, ab_type);
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
                AbilityInstance* vi_ab = get_ability(state.players[pid], CHAR_VillageIdiot);
                if (vi_ab != nullptr) {
                    vis[n_vis++] = pid;
                    if (vi_ab->self_droison) {
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
                if (AbilityInstance* vi_ab = get_ability(drunk_vi, CHAR_VillageIdiot)) {
                    vi_ab->self_droison = true;
                }
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
                get_ability_ref(new_state, me, ab_type).target = pid;
                yield(new_state);
            }
            return;
        }

        case CHAR_Puzzlemaster: {
            for (PlayerID pid = 0; pid < N; ++pid) {
                State new_state = state;
                AbilityInstance& pm = get_ability_ref(new_state, me, ab_type);
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

inline bool pithag_can_register_as_demon(CharacterID c) {
    return is_category(c, CAT_DEMON) || ((CHAR_META[c].misregister_categories & CAT_DEMON) != 0);
}

void pithag_kill_all_remaining_deaths(State& state, PlayerID me, YieldFn yield) {
    PlayerID deaths[MAX_DEATHS_PER_NIGHT];
    int n_deaths = 0;
    uint8_t nd_count = state.puzzle->night_death_counts[state.night];
    const NightDeathNode* nds = state.puzzle->night_deaths[state.night];
    for (uint8_t i = 0; i < nd_count; ++i) {
        if (!nds[i].is_resurrection && eval_is_alive(state, nds[i].player, me).is_true()) {
            deaths[n_deaths++] = nds[i].player;
        }
    }
    auto step = [&](State& s, int idx, YieldFn y) {
        attacked_at_night(s, deaths[idx], me, y);
    };
    apply_seq(state, 0, n_deaths, step, yield);
}

void pithag_arbitrary_deaths(State& state, PlayerID me, YieldFn yield) {
    if (state.pithag_preventing_kills == me) {
        state.pithag_kills_at_night_end = me;
        yield(state);
        return;
    }
    State later_state = state;
    later_state.pithag_kills_at_night_end = me;
    yield(later_state);

    auto after_kills = [&](State& substate) {
        substate.pithag_preventing_kills = me;
        yield(substate);
    };
    pithag_kill_all_remaining_deaths(state, me, make_yield(after_kills));
}

void run_character_night(State& state, PlayerID me, YieldFn yield, CharacterID which_ability = CHAR_NONE) {
    Player& player = state.players[me];
    AbilityInstance& ab = get_ability_ref(state, me, which_ability);
    CharacterID ab_type = ab.type;
    int N = state.puzzle->num_players;

    if (ab_type == CHAR_Philosopher) {
        if (player.has_philo_ability) {
            run_character_night(state, me, yield, player.philo_ability.type);
            return;
        }
        if (ab.aux_bool) {
            CharacterID sim_t = player.drunklike_char.type;
            if (get_night_info(state, sim_t, me, state.night) != -1
                || wakes_tonight_ability(state, player.drunklike_char, me)) {
                math_misregistration(state, me);
            }
            drunklike_run_simulation(state, me, yield);
            return;
        }
        if (player.is_dead) {
            yield(state);
            return;
        }
        if (!lies_about_info(state, me)) {
            int16_t choice_idx = get_night_info(state, CHAR_Philosopher, me, state.night);
            if (choice_idx == -1) {
                yield(state);
                return;
            }
            CharacterID chosen_char = state.puzzle->info_nodes[choice_idx].character1;
            philo_choose_ability(state, me, chosen_char, yield);
            return;
        }
        for (int i = 0; i < state.puzzle->num_script; ++i) {
            CharacterID c = state.puzzle->script[i];
            if (is_category(c, CAT_TOWNSFOLK | CAT_OUTSIDER) && c != CHAR_Philosopher) {
                State new_state = state;
                philo_choose_ability(new_state, me, c, yield);
            }
        }
        yield(state);
        return;
    }

    if (ab_type == CHAR_Hermit) {
        if (hermit_has_outsider(CHAR_Lunatic)
            && (state.currently_acting_character == CHAR_Lunatic
                || (player.has_drunklike_char && state.currently_acting_character == player.drunklike_char.type))) {
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
        if (hermit_has_outsider(CHAR_Drunk)
            && (state.currently_acting_character == CHAR_Drunk
                || (player.has_drunklike_char && state.currently_acting_character == player.drunklike_char.type))) {
            drunklike_run_simulation(state, me, yield);
            return;
        }
        if (default_info_check(state, ab, me, false, false)) {
            yield(state);
        }
        return;
    }

    if (CHAR_META[ab_type].is_drunklike) {
        if (ab_type == CHAR_Lunatic) {
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

    switch (ab_type) {
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

        case CHAR_Widow: {
            if (state.night == ab.first_night) {
                widow_run_first_night(state, ab, me, yield);
            } else {
                uint8_t ext_count = state.puzzle->external_info_count[state.night][CHAR_Widow];
                const ExternalInfoEntry* ext_entries = state.puzzle->external_info[state.night][CHAR_Widow];
                for (uint8_t i = 0; i < ext_count; ++i) {
                    if (!behaves_evil(state, ext_entries[i].player_id)) {
                        return;
                    }
                }
                yield(state);
            }
            return;
        }

        case CHAR_Exorcist: {
            if (player.is_dead) {
                yield(state);
                return;
            }
            int16_t choice_idx = get_night_info(state, CHAR_Exorcist, me, state.night);
            if (choice_idx == -1) {
                yield(state);
                return;
            }
            PlayerID chosen = state.puzzle->info_nodes[choice_idx].player1;
            maybe_deactivate_effects(state, ab, me);
            ab.target = chosen;
            bool would_wake = wakes_tonight_ability(state, state.players[chosen].character, chosen);
            maybe_activate_effects(state, ab, me);

            STBool is_demon = eval_is_category(state, chosen, CAT_DEMON, false, me);
            if (is_demon.is_false()) {
                yield(state);
                return;
            }
            if (is_demon.is_maybe()) {
                State forked = state;
                yield(forked);
            }
            if (is_droisoned(state, ab, me)) {
                math_misregistration(state, me);
            } else if (would_wake) {
                math_misregistration(state, chosen);
            }
            yield(state);
            return;
        }

        case CHAR_DevilsAdvocate: {
            PlayerID prev_target = ab.target;
            maybe_deactivate_effects(state, ab, me);
            ab.target = NONE_PLAYER;
            if (player.is_dead && !ab.vigormortised) {
                yield(state);
                return;
            }
            if (is_droisoned(state, ab, me)) {
                STBool tm = STBoolVal::TRUE_MAYBE;
                math_misregistration(state, me, &tm);
                yield(state);
                return;
            }
            PlayerID executed_today = NONE_PLAYER;
            int ev_count = state.puzzle->day_event_counts[state.night];
            const EventNode* evs = state.puzzle->day_events[state.night];
            for (int i = 0; i < ev_count; ++i) {
                if (evs[i].type == EVENT_EXECUTION || evs[i].type == EVENT_EXECUTION_BY_ST) {
                    executed_today = evs[i].player;
                    break;
                }
            }
            for (PlayerID target = 0; target < N; ++target) {
                if (target != prev_target && target != executed_today && !state.players[target].is_dead) {
                    State new_state = state;
                    AbilityInstance& new_da = get_ability_ref(new_state, me, ab_type);
                    new_da.target = target;
                    maybe_activate_effects(new_state, new_da, me);
                    yield(new_state);
                    break;
                }
            }
            if (executed_today != NONE_PLAYER && executed_today != prev_target) {
                ab.target = executed_today;
                maybe_activate_effects(state, ab, me);
                yield(state);
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
                AbilityInstance& new_ab = get_ability_ref(new_state, me, ab_type);
                new_ab.target = target;
                if (np.history_len < MAX_NIGHTS) {
                    np.target_history[np.history_len++] = target;
                }
                maybe_activate_effects(new_state, new_ab, me);
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

        case CHAR_FangGu: {
            if (state.night == 1 || player.is_dead || player.exorcised_count > 0) {
                yield(state);
                return;
            }
            PlayerID base_targets[MAX_PLAYERS];
            int n_base = generic_demon_get_targets(state, me, base_targets);
            uint16_t target_mask = 0;
            for (int i = 0; i < n_base; ++i) {
                target_mask |= static_cast<uint16_t>(1u << base_targets[i]);
            }
            for (PlayerID pid = 0; pid < N; ++pid) {
                if (!state.players[pid].is_dead && eval_is_category(state, pid, CAT_OUTSIDER, false, me).not_false()) {
                    target_mask |= static_cast<uint16_t>(1u << pid);
                }
            }
            PlayerID targets[MAX_PLAYERS];
            int n_targets = 0;
            for (PlayerID pid = 0; pid < N; ++pid) {
                if (target_mask & (1u << pid)) {
                    targets[n_targets++] = pid;
                }
            }
            bool sunk_a_kill = false;
            for (int i = 0; i < n_targets; ++i) {
                PlayerID target = targets[i];
                const Player& target_player = state.players[target];
                if (target_player.is_dead) {
                    if (sunk_a_kill) continue;
                    State sink_state = state;
                    yield(sink_state);
                    sunk_a_kill = true;
                    continue;
                }
                if (is_droisoned(state, ab, me)) {
                    State droison_state = state;
                    math_misregistration(droison_state, me);
                    yield(droison_state);
                    break;
                }
                STBool is_outsider = eval_is_category(state, target, CAT_OUTSIDER, false, me);
                STBool tries_jump = is_outsider & STBool(!state.fanggu_already_jumped);
                STBool jump_thwarted = safe_from_attacker(state, me, me) | safe_from_attacker(state, target, me);
                STBool jumps = tries_jump & ~jump_thwarted;

                if (jumps.not_true()) {
                    State kill_state = state;
                    if (is_category(target_player.character.type, CAT_OUTSIDER) && tries_jump.not_false()) {
                        math_misregistration(kill_state, me);
                    }
                    attacked_at_night(kill_state, target, me, yield);
                }
                if (jumps.not_false()) {
                    State jump_state = state;
                    jump_state.fanggu_already_jumped = true;
                    if (!is_category(target_player.character.type, CAT_OUTSIDER)) {
                        math_misregistration(jump_state, me);
                    }
                    auto after_char = [&](State& ss_) {
                        auto after_align = [&](State& ss) {
                            apply_death(ss, me, me, yield);
                        };
                        change_alignment(ss_, target, true, make_yield(after_align));
                    };
                    change_character(jump_state, target, CHAR_FangGu, make_yield(after_char));
                }
            }
            return;
        }

        case CHAR_Vigormortis: {
            if (state.night == 1 || player.is_dead || player.exorcised_count > 0) {
                yield(state);
                return;
            }
            bool sunk_a_kill = false;
            for (PlayerID target = 0; target < N; ++target) {
                const Player& target_player = state.players[target];
                if (target_player.is_dead) {
                    if (sunk_a_kill) continue;
                    State sink_state = state;
                    yield(sink_state);
                    sunk_a_kill = true;
                    continue;
                }
                if (is_droisoned(state, ab, me)) {
                    State droison_state = state;
                    math_misregistration(droison_state, me);
                    yield(droison_state);
                    continue;
                }
                STBool is_minion = eval_is_category(state, target, CAT_MINION, false, me);
                if (is_minion.not_true()) {
                    State kill_state = state;
                    attacked_at_night(kill_state, target, me, yield);
                    if (is_minion.is_false()) {
                        continue;
                    }
                }
                State minion_state = state;
                minion_state.players[target].character.vigormortised = true;
                if (minion_state.players[target].has_philo_ability) {
                    minion_state.players[target].philo_ability.vigormortised = true;
                }
                PlayerID bkwd_tf[MAX_PLAYERS];
                PlayerID fwd_tf[MAX_PLAYERS];
                int n_bkwd = tf_to_droison_in_direction(minion_state, target, -1, bkwd_tf);
                int n_fwd = tf_to_droison_in_direction(minion_state, target, 1, fwd_tf);
                PlayerID candidates[MAX_PLAYERS * 2];
                int n_cand = 0;
                for (int bi = 0; bi < n_bkwd; ++bi) candidates[n_cand++] = bkwd_tf[bi];
                for (int fi = 0; fi < n_fwd; ++fi) candidates[n_cand++] = fwd_tf[fi];

                auto after_attack = [&](State& ss1) {
                    for (int ci = 0; ci < n_cand; ++ci) {
                        PlayerID poison_candidate = candidates[ci];
                        State ss2 = ss1;
                        AbilityInstance& new_vig = get_ability_ref(ss2, me, ab_type);
                        maybe_activate_effects(ss2, new_vig, me);
                        new_vig.aux_mask |= static_cast<uint16_t>(1u << target);
                        new_vig.vig_poisoned_mask |= static_cast<uint16_t>(1u << poison_candidate);
                        if (new_vig.effects_active) {
                            droison_player(ss2, poison_candidate, me);
                        }
                        yield(ss2);
                    }
                };
                attacked_at_night(minion_state, target, me, make_yield(after_attack));
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
                AbilityInstance& new_ab = get_ability_ref(new_state, me, ab_type);
                new_ab.target = new_target;
                if (np.history_len < MAX_NIGHTS) {
                    np.target_history[np.history_len++] = new_target;
                }
                maybe_activate_effects(new_state, new_ab, me);
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
                get_ability_ref(charge_state, me, ab_type).aux_bool = true;
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
                    AbilityInstance& new_c = get_ability_ref(new_state, me, ab_type);
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
                AbilityInstance& new_c = get_ability_ref(new_state, me, ab_type);
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
            AbilityInstance& jump_ab = get_ability_ref(jump_state, me, ab_type);
            if (is_droisoned(jump_state, jump_ab, me)) {
                if (!jump_ab.self_droison) {
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
                    get_ability_ref(spent_world, me, ab_type).spent = true;
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
                AbilityInstance& new_witch = get_ability_ref(new_state, me, ab_type);
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
                AbilityInstance& new_xaan = get_ability_ref(new_state, me, ab_type);
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

        case CHAR_Monk: {
            if (state.night == 1) {
                yield(state);
                return;
            }
            PlayerID targets[MAX_PLAYERS];
            int n_targets = 0;
            if (lies_about_info(state, me)) {
                if (player.is_dead) {
                    yield(state);
                    return;
                }
                for (PlayerID p = 0; p < N; ++p) {
                    if (p != me) targets[n_targets++] = p;
                }
            } else {
                int16_t choice_idx = get_night_info(state, CHAR_Monk, me, state.night);
                if (choice_idx == -1) {
                    yield(state);
                    return;
                }
                if (player.is_dead) {
                    return;
                }
                PlayerID chosen = state.puzzle->info_nodes[choice_idx].player1;
                if (chosen == me) {
                    return;
                }
                targets[n_targets++] = chosen;
            }
            for (int i = 0; i < n_targets; ++i) {
                PlayerID target = targets[i];
                State new_state = state;
                Player& np = new_state.players[me];
                AbilityInstance& new_monk = get_ability_ref(new_state, me, ab_type);
                maybe_deactivate_effects(new_state, new_monk, me);
                new_monk.target = target;
                if (np.history_len < MAX_NIGHTS) {
                    np.target_history[np.history_len++] = target;
                }
                maybe_activate_effects(new_state, new_monk, me);
                yield(new_state);
            }
            return;
        }

        case CHAR_Cerenovus: {
            if (player.is_dead && !ab.vigormortised) {
                yield(state);
                return;
            }
            if (is_droisoned(state, ab, me)) {
                math_misregistration(state, me);
                ab.target = NONE_PLAYER;
                yield(state);
                return;
            }
            uint16_t target_mask = 0;
            PlayerID first_evil = NONE_PLAYER;
            for (PlayerID pid = 0; pid < N; ++pid) {
                if (behaves_evil(state, pid)) {
                    if (first_evil == NONE_PLAYER) first_evil = pid;
                }
                if (state.players[pid].speculative_ceremad) {
                    target_mask |= static_cast<uint16_t>(1u << pid);
                }
            }
            uint8_t ext_count = state.puzzle->external_info_count[state.night][CHAR_Cerenovus];
            const ExternalInfoEntry* ext_entries = state.puzzle->external_info[state.night][CHAR_Cerenovus];
            for (uint8_t i = 0; i < ext_count; ++i) {
                PlayerID pid = ext_entries[i].player_id;
                if (!behaves_evil(state, pid)) {
                    target_mask |= static_cast<uint16_t>(1u << pid);
                }
            }
            if (state.night + 1 < MAX_NIGHTS) {
                int ev_count = state.puzzle->day_event_counts[state.night + 1];
                const EventNode* evs = state.puzzle->day_events[state.night + 1];
                for (int i = 0; i < ev_count; ++i) {
                    if (evs[i].player >= 0 && evs[i].player < N) {
                        target_mask |= static_cast<uint16_t>(1u << evs[i].player);
                    }
                }
            }
            if (first_evil != NONE_PLAYER) {
                target_mask |= static_cast<uint16_t>(1u << first_evil);
            }
            for (PlayerID target = 0; target < N; ++target) {
                if (!(target_mask & (1u << target))) continue;
                State new_state = state;
                Player& np = new_state.players[me];
                AbilityInstance& new_cere = get_ability_ref(new_state, me, ab_type);
                new_cere.target = target;
                if (np.history_len < MAX_NIGHTS) {
                    np.target_history[np.history_len++] = target;
                }
                maybe_activate_effects(new_state, new_cere, me);
                change_claim_if_claimed_change_tonight(new_state, target);
                yield(new_state);
            }
            return;
        }

        case CHAR_PitHag: {
            if (state.night == 1 || (player.is_dead && !ab.vigormortised)) {
                yield(state);
                return;
            }
            if (is_droisoned(state, ab, me)) {
                STBool fm = STBoolVal::FALSE_MAYBE;
                math_misregistration(state, me, &fm);
                yield(state);
                return;
            }
            CharacterID not_in_play[MAX_SCRIPT];
            int n_nip = 0;
            CharacterID lying_chars[MAX_SCRIPT];
            int n_lying = 0;
            for (int i = 0; i < state.puzzle->num_script; ++i) {
                CharacterID c = state.puzzle->script[i];
                if (eval_is_in_play(state, c, me).not_true()) {
                    not_in_play[n_nip++] = c;
                    if (CHAR_META[c].lies_about_character_and_info) {
                        lying_chars[n_lying++] = c;
                    }
                }
            }
            CharacterID evil_targets[MAX_SCRIPT];
            int n_evil_targets = 0;
            if (state.pithag_preventing_kills == me) {
                for (int i = 0; i < n_nip; ++i) {
                    if (pithag_can_register_as_demon(not_in_play[i])) {
                        evil_targets[n_evil_targets++] = not_in_play[i];
                    }
                }
            } else {
                for (int i = 0; i < n_nip; ++i) {
                    evil_targets[n_evil_targets++] = not_in_play[i];
                }
            }

            for (PlayerID target = 0; target < N; ++target) {
                CharacterID cands[MAX_SCRIPT];
                int n_cands = 0;
                if (lies_about_character(state, target)) {
                    for (int i = 0; i < n_evil_targets; ++i) {
                        cands[n_cands++] = evil_targets[i];
                    }
                } else {
                    for (int i = 0; i < n_lying; ++i) {
                        cands[n_cands++] = lying_chars[i];
                    }
                    int16_t cc_idx = get_night_info(state, CHAR_NONE, target, state.night);
                    if (cc_idx != -1) {
                        const InfoNode& cc = state.puzzle->info_nodes[cc_idx];
                        if (cc.type == NOTINFO_CHARACTER_CHANGE) {
                            bool already = false;
                            for (int i = 0; i < n_cands; ++i) {
                                if (cands[i] == cc.character1) { already = true; break; }
                            }
                            if (!already) cands[n_cands++] = cc.character1;
                        }
                    }
                }
                for (int ci = 0; ci < n_cands; ++ci) {
                    CharacterID char_t = cands[ci];
                    State new_state = state;
                    Player& np = new_state.players[me];
                    if (np.history_len < MAX_NIGHTS) {
                        np.target_history[np.history_len] = target;
                        np.target_char_history[np.history_len] = char_t;
                        np.history_len++;
                    }
                    auto after_change = [&](State& substate) {
                        if (pithag_can_register_as_demon(char_t)) {
                            pithag_arbitrary_deaths(substate, me, yield);
                        } else {
                            yield(substate);
                        }
                    };
                    change_character(new_state, target, char_t, make_yield(after_change));
                }
            }
            if (state.pithag_preventing_kills != me) {
                if (player.history_len < MAX_NIGHTS) {
                    player.target_history[player.history_len] = NONE_PLAYER;
                    player.target_char_history[player.history_len] = CHAR_NONE;
                    player.history_len++;
                }
                yield(state);
            }
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

void run_character_day(State& state, PlayerID me, YieldFn yield, CharacterID which_ability = CHAR_NONE) {
    Player& player = state.players[me];
    AbilityInstance& ab = get_ability_ref(state, me, which_ability);
    CharacterID ab_type = ab.type;

    if (ab_type == CHAR_Philosopher) {
        if (player.has_philo_ability) {
            run_character_day(state, me, yield, player.philo_ability.type);
            return;
        }
        if (ab.aux_bool && get_day_info(state, player.drunklike_char.type, me) != -1) {
            math_misregistration(state, me);
        }
        yield(state);
        return;
    }

    if (ab_type == CHAR_Riot) {
        if (state.day != 3 || player.is_dead) {
            yield(state);
            return;
        }
        if (is_droisoned(state, ab, me)) {
            math_misregistration(state, me);
            yield(state);
            return;
        }
        maybe_deactivate_effects(state, ab, me);
        maybe_activate_effects(state, ab, me);
        if (player.exorcised_count > 0) {
            yield(state);
            return;
        }

        int N = state.puzzle->num_players;
        uint16_t trues_mask = 0;
        PlayerID maybes[MAX_PLAYERS];
        int n_maybes = 0;
        for (PlayerID pid = 0; pid < N; ++pid) {
            STBool is_m = eval_is_category(state, pid, CAT_MINION, false, me);
            if (is_m.is_true()) {
                trues_mask |= static_cast<uint16_t>(1u << pid);
            } else if (is_m.is_maybe()) {
                maybes[n_maybes++] = pid;
            }
        }

        int num_subsets = 1 << n_maybes;
        for (int mask = 0; mask < num_subsets; ++mask) {
            uint16_t subset_mask = trues_mask;
            for (int b = 0; b < n_maybes; ++b) {
                if (mask & (1 << b)) {
                    subset_mask |= static_cast<uint16_t>(1u << maybes[b]);
                }
            }
            PlayerID minions[MAX_PLAYERS];
            int n_minions = 0;
            for (PlayerID pid = 0; pid < N; ++pid) {
                if (subset_mask & (1u << pid)) {
                    minions[n_minions++] = pid;
                }
            }
            State comb_state = state;
            auto make_riot_step = [&](State& s, int idx, YieldFn y) {
                PlayerID m_pid = minions[idx];
                auto after_change = [&](State& ss) {
                    maybe_activate_effects(ss, ss.players[m_pid].character, m_pid, REASON_CHARACTER_CHANGE);
                    y(ss);
                };
                change_character(s, m_pid, CHAR_Riot, make_yield(after_change));
            };
            apply_seq(comb_state, 0, n_minions, make_riot_step, yield);
        }
        return;
    }

    if (ab_type == CHAR_Savant) {
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

    if (ab_type == CHAR_Hermit) {
        if (state.currently_acting_character == CHAR_Mutant && hermit_has_outsider(CHAR_Mutant)) {
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
        if (state.currently_acting_character == CHAR_Puzzlemaster && hermit_has_outsider(CHAR_Puzzlemaster)) {
            if (default_info_check(state, ab, me, false, false)) {
                yield(state);
            }
            return;
        }
        yield(state);
        return;
    }

    if (ab_type == CHAR_Mutant) {
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

void run_ability_end_night(State& state, PlayerID me, AbilityInstance& ab, YieldFn yield) {
    Player& player = state.players[me];
    switch (ab.type) {
        case CHAR_Philosopher:
            if (player.has_philo_ability) {
                run_ability_end_night(state, me, player.philo_ability, yield);
            } else {
                yield(state);
            }
            return;
        case CHAR_Hermit:
            if (hermit_has_outsider(CHAR_Drunk)) {
                change_claim_if_claimed_change_tonight(state, me);
                if (is_category(player.claim, CAT_TOWNSFOLK) || lies_about_character(state, me, true)) {
                    yield(state);
                }
                return;
            }
            yield(state);
            return;
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
        case CHAR_PitHag:
            state.pithag_preventing_kills = NONE_PLAYER;
            if (state.pithag_kills_at_night_end != NONE_PLAYER) {
                state.pithag_kills_at_night_end = NONE_PLAYER;
                pithag_kill_all_remaining_deaths(state, me, yield);
            } else {
                yield(state);
            }
            return;
        default:
            yield(state);
            return;
    }
}

void run_character_end_night(State& state, PlayerID me, YieldFn yield) {
    run_ability_end_night(state, me, state.players[me].character, yield);
}

void run_ability_end_day(State& state, PlayerID me, AbilityInstance& ab, YieldFn yield) {
    Player& player = state.players[me];
    switch (ab.type) {
        case CHAR_Philosopher:
            if (player.has_philo_ability) {
                run_ability_end_day(state, me, player.philo_ability, yield);
            } else {
                yield(state);
            }
            return;
        case CHAR_Poisoner:
        case CHAR_Cerenovus:
            maybe_deactivate_effects(state, ab, me);
            ab.target = NONE_PLAYER;
            yield(state);
            return;
        case CHAR_PitHag: {
            if (state.day == state.puzzle->max_night) {
                yield(state);
                return;
            }
            bool can_make_demon = false;
            for (int i = 0; i < state.puzzle->num_script; ++i) {
                CharacterID c = state.puzzle->script[i];
                if (pithag_can_register_as_demon(c) && eval_is_in_play(state, c, me).not_true()) {
                    can_make_demon = true;
                    break;
                }
            }
            if (!can_make_demon) {
                yield(state);
                return;
            }
            State arb_state = state;
            arb_state.pithag_preventing_kills = me;
            yield(arb_state);
            yield(state);
            return;
        }
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

void run_character_end_day(State& state, PlayerID me, YieldFn yield) {
    run_ability_end_day(state, me, state.players[me].character, yield);
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
    } else if (char_t == CHAR_Widow) {
        bool widow_in_play = false;
        for (PlayerID pid = 0; pid < state.puzzle->num_players; ++pid) {
            if (has_ability(state.players[pid], CHAR_Widow)) {
                widow_in_play = true;
                break;
            }
        }
        if (!widow_in_play) {
            uint8_t ext_count = state.puzzle->external_info_count[state.night][CHAR_Widow];
            const ExternalInfoEntry* ext_entries = state.puzzle->external_info[state.night][CHAR_Widow];
            for (uint8_t i = 0; i < ext_count; ++i) {
                if (!behaves_evil(state, ext_entries[i].player_id)) {
                    return false;
                }
            }
        }
    } else if (char_t == CHAR_Cerenovus) {
        if (state.night == state.puzzle->max_night) {
            return true;
        }
        uint16_t claiming_mask = 0;
        uint8_t ext_count = state.puzzle->external_info_count[state.night][CHAR_Cerenovus];
        const ExternalInfoEntry* ext_entries = state.puzzle->external_info[state.night][CHAR_Cerenovus];
        for (uint8_t i = 0; i < ext_count; ++i) {
            claiming_mask |= static_cast<uint16_t>(1u << ext_entries[i].player_id);
        }
        for (PlayerID pid = 0; pid < state.puzzle->num_players; ++pid) {
            const Player& p = state.players[pid];
            if (p.ceremad > 0
                && !(claiming_mask & (1u << pid))
                && !p.speculative_ceremad
                && !behaves_evil(state, pid)) {
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
    CharacterID which_ab = ab->type;

    auto recurse = [&](State& substate) {
        run_all_players_with_currently_acting_character(substate, yield);
    };
    YieldFn next_yield = make_yield(recurse);

    switch (state.current_phase) {
        case PHASE_NIGHT:
            if (wakes_tonight_ability(state, *ab, pid)) {
                player.woke_tonight = true;
            }
            run_character_night(state, pid, next_yield, which_ab);
            break;
        case PHASE_DAY:
            run_character_day(state, pid, next_yield, which_ab);
            break;
        case PHASE_SETUP:
            run_character_setup(state, pid, next_yield, which_ab);
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
            case EXTINFO_POPPYGROWER_IN_PLAY: {
                bool pg_active = false;
                for (PlayerID p = 0; p < state.puzzle->num_players; ++p) {
                    const AbilityInstance* pg = get_ability(state.players[p], CHAR_PoppyGrower);
                    if (pg != nullptr && !is_droisoned(state, *pg, p)) {
                        pg_active = true;
                        break;
                    }
                }
                ok = (state.players[pid].is_evil && pg_active);
                break;
            }
            case EXTINFO_EVILTWIN_IS: {
                const AbilityInstance* et = get_ability(state.players[node.player1], CHAR_EvilTwin);
                ok = (et != nullptr && et->target == pid);
                break;
            }
            case EXTINFO_CERENOVUS_MAD: {
                if (state.players[pid].ceremad == 0) {
                    ok = false;
                    break;
                }
                bool found = false;
                for (PlayerID p = 0; p < state.puzzle->num_players; ++p) {
                    const AbilityInstance* c = get_ability(state.players[p], CHAR_Cerenovus);
                    if (c != nullptr && c->target == pid) {
                        found = true;
                        break;
                    }
                }
                ok = found;
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
                if (golem->type == CHAR_Hermit) {
                    golem->aux_bool = true;
                } else {
                    golem->spent = true;
                }
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
                    if (golem->type == CHAR_Hermit) {
                        golem->aux_bool = true;
                    } else {
                        golem->spent = true;
                    }
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

        case EVENT_FLOWERGIRL_VOTERS: {
            STBool demon_voted = STBoolVal::FALSE;
            for (int i = 0; i < ev.count; ++i) {
                demon_voted |= eval_is_category(state, ev.players[i], CAT_DEMON, false, ev.player);
            }
            Player& fg = state.players[ev.player];
            fg.saved_day_bool = demon_voted;
            fg.saved_day_num = state.day;
            yield(state);
            return;
        }

        case EVENT_TOWNCRIER_NOMINATORS: {
            STBool minion_nominated = STBoolVal::FALSE;
            for (int i = 0; i < ev.count; ++i) {
                minion_nominated |= eval_is_category(state, ev.players[i], CAT_MINION, false, ev.player);
            }
            Player& tc = state.players[ev.player];
            tc.saved_day_bool = minion_nominated;
            tc.saved_day_num = state.day;
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

struct SolveJob;

void round_robin(
    State& state,
    const SimSchedule& sched,
    const StartingConfig& config,
    YieldFn yield,
    SolveJob* ws = nullptr,
    int worker_id = 0
) {
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
            world_check_with_sched(*state.puzzle, sched, redo, yield, ws, worker_id);
            return;
        }
    }
    yield(state);
}

struct SolveTask {
    State state;
    StartingConfig config;
    int step_idx;
};

struct alignas(64) WorkerQueue {
    std::mutex mtx;
    std::deque<SolveTask> q;
};

struct SolveJob {
    const SerializedPuzzle* puzzle = nullptr;
    const SimSchedule* sched = nullptr;
    const std::vector<StartingConfig>* configs = nullptr;
    SerializedSolution* out_solutions = nullptr;
    int max_solutions = 0;
    int num_workers = 1;

    std::atomic<size_t> next_config{0};
    std::atomic<int64_t> in_flight{0};
    std::atomic<int64_t> pending_stealable{0};
    std::atomic<int> idle_workers{0};
    std::atomic<bool> done{false};

    std::mutex wait_mtx;
    std::condition_variable wait_cv;
    std::deque<WorkerQueue> queues;

    std::mutex sol_mtx;
    int num_solutions = 0;
    std::vector<SolutionKey> seen_keys;

    SolveJob(
        const SerializedPuzzle* p,
        const SimSchedule* s,
        const std::vector<StartingConfig>* cfgs,
        SerializedSolution* out,
        int max_sols,
        int workers
    ) : puzzle(p), sched(s), configs(cfgs), out_solutions(out), max_solutions(max_sols), num_workers(workers) {
        in_flight.store(static_cast<int64_t>(cfgs->size()), std::memory_order_relaxed);
        for (int i = 0; i < workers; ++i) {
            queues.emplace_back();
        }
    }

    void push_task(int worker_id, const State& st, const StartingConfig& cfg, int step_idx) {
        in_flight.fetch_add(1, std::memory_order_relaxed);
        {
            std::lock_guard<std::mutex> lk(queues[worker_id].mtx);
            queues[worker_id].q.push_back(SolveTask{st, cfg, step_idx});
        }
        pending_stealable.fetch_add(1, std::memory_order_release);
        if (idle_workers.load(std::memory_order_acquire) > 0) {
            {
                std::lock_guard<std::mutex> lk(wait_mtx);
            }
            wait_cv.notify_one();
        }
    }

    bool pop_local(int worker_id, SolveTask& out) {
        std::lock_guard<std::mutex> lk(queues[worker_id].mtx);
        if (queues[worker_id].q.empty()) return false;
        out = queues[worker_id].q.back();
        queues[worker_id].q.pop_back();
        pending_stealable.fetch_sub(1, std::memory_order_relaxed);
        return true;
    }

    bool steal_from(int victim_id, SolveTask& out) {
        std::unique_lock<std::mutex> lk(queues[victim_id].mtx, std::try_to_lock);
        if (!lk.owns_lock() || queues[victim_id].q.empty()) return false;
        out = queues[victim_id].q.front();
        queues[victim_id].q.pop_front();
        pending_stealable.fetch_sub(1, std::memory_order_relaxed);
        return true;
    }

    void complete_one() {
        if (in_flight.fetch_sub(1, std::memory_order_acq_rel) == 1) {
            {
                std::lock_guard<std::mutex> lk(wait_mtx);
                done.store(true, std::memory_order_release);
            }
            wait_cv.notify_all();
        }
    }

    void record_solution(const State& sol) {
        std::lock_guard<std::mutex> lk(sol_mtx);
        int N = puzzle->num_players;
        if (puzzle->deduplicate_initial_characters) {
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
                sp.ceremad = p.ceremad;
                sp.vigormortised = p.character.vigormortised ? 1 : 0;
                sp.self_droison = p.character.self_droison ? 1 : 0;
                sp.target = p.character.target;
                sp.aux_target = p.character.aux_target;
                sp.history_len = p.history_len;
                for (int h = 0; h < p.history_len && h < MAX_NIGHTS; ++h) {
                    sp.target_history[h] = p.target_history[h];
                    sp.target_char_history[h] = p.target_char_history[h];
                }
                sp.char_history_len = 0;
            }
            for (uint8_t c = 0; c < sol.num_char_changes; ++c) {
                const CharChangeEntry& e = sol.char_changes[c];
                if (e.pid >= 0 && e.pid < N) {
                    SerializedSolutionPlayer& sp = out.players[e.pid];
                    if (sp.char_history_len < MAX_NIGHTS) {
                        uint8_t h = sp.char_history_len++;
                        sp.char_history[h] = e.prev_char;
                        sp.char_history_phase[h] = static_cast<uint8_t>(e.phase_and_round >> 6);
                        sp.char_history_round[h] = static_cast<int8_t>(e.phase_and_round & 0x3Fu);
                    }
                }
            }
        }
    }
};

void execute_step(
    State& state,
    const SimSchedule& sched,
    const SimStep& step,
    const StartingConfig& config,
    YieldFn next_yield,
    SolveJob* ws,
    int worker_id
) {
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
            round_robin(state, sched, config, next_yield, ws, worker_id);
            break;
    }
}

void run_schedule(
    State& state,
    const SimSchedule& sched,
    int step_idx,
    const StartingConfig& config,
    YieldFn solution_yield,
    SolveJob* ws = nullptr,
    int worker_id = 0
) {
    if (step_idx >= sched.num_steps) {
        solution_yield(state);
        return;
    }
    const SimStep& step = sched.steps[step_idx];
    if (ws == nullptr || step_idx + 2 >= sched.num_steps
        || ws->idle_workers.load(std::memory_order_relaxed) == 0) {
        auto next = [&](State& substate) {
            run_schedule(substate, sched, step_idx + 1, config, solution_yield, ws, worker_id);
        };
        YieldFn next_yield = make_yield(next);
        execute_step(state, sched, step, config, next_yield, ws, worker_id);
        return;
    }

    // Demand-driven work-stealing split: keep the first child inline so non-branching
    // steps have zero queue overhead, and offload sibling branches while workers are idle.
    bool has_first = false;
    State first_child;
    auto next = [&](State& substate) {
        if (!has_first) {
            first_child = substate;
            has_first = true;
        } else if (ws->idle_workers.load(std::memory_order_relaxed) > 0) {
            ws->push_task(worker_id, substate, config, step_idx + 1);
        } else {
            run_schedule(substate, sched, step_idx + 1, config, solution_yield, ws, worker_id);
        }
    };
    YieldFn next_yield = make_yield(next);
    execute_step(state, sched, step, config, next_yield, ws, worker_id);
    if (has_first) {
        run_schedule(first_child, sched, step_idx + 1, config, solution_yield, ws, worker_id);
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
                || (char_lies_about_character_and_info(p)
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

void world_check_with_sched(
    const SerializedPuzzle& puzzle,
    const SimSchedule& sched,
    const StartingConfig& config,
    YieldFn yield,
    SolveJob* ws = nullptr,
    int worker_id = 0
) {
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

    run_schedule(world, sched, 0, config, yield, ws, worker_id);
}

void run_worker(SolveJob& job, int worker_id) {
    g_current_puzzle = job.puzzle;
    auto on_sol = [&](State& sol) {
        job.record_solution(sol);
    };
    YieldFn sol_yield = make_yield(on_sol);

    uint32_t rng = 0x9e3779b9u * static_cast<uint32_t>(worker_id + 1);
    auto next_rng = [&]() -> uint32_t {
        rng ^= rng << 13;
        rng ^= rng >> 17;
        rng ^= rng << 5;
        return rng;
    };

    while (!job.done.load(std::memory_order_acquire)) {
        SolveTask task;
        if (job.pop_local(worker_id, task)) {
            run_schedule(task.state, *job.sched, task.step_idx, task.config, sol_yield, &job, worker_id);
            job.complete_one();
            continue;
        }

        size_t cfg_idx = job.next_config.fetch_add(1, std::memory_order_relaxed);
        if (cfg_idx < job.configs->size()) {
            world_check_with_sched(*job.puzzle, *job.sched, (*job.configs)[cfg_idx], sol_yield, &job, worker_id);
            job.complete_one();
            continue;
        }

        job.idle_workers.fetch_add(1, std::memory_order_acq_rel);
        bool stole = false;
        for (int attempt = 0; attempt < 32 && !job.done.load(std::memory_order_acquire); ++attempt) {
            int start = static_cast<int>(next_rng() % static_cast<uint32_t>(job.num_workers));
            for (int off = 0; off < job.num_workers; ++off) {
                int victim = (start + off) % job.num_workers;
                if (victim == worker_id) continue;
                if (job.steal_from(victim, task)) {
                    stole = true;
                    break;
                }
            }
            if (stole) break;
            std::this_thread::yield();
        }
        if (stole) {
            job.idle_workers.fetch_sub(1, std::memory_order_relaxed);
            run_schedule(task.state, *job.sched, task.step_idx, task.config, sol_yield, &job, worker_id);
            job.complete_one();
            continue;
        }

        {
            std::unique_lock<std::mutex> lk(job.wait_mtx);
            job.wait_cv.wait(lk, [&]() {
                return job.done.load(std::memory_order_acquire)
                    || job.pending_stealable.load(std::memory_order_acquire) > 0;
            });
        }
        job.idle_workers.fetch_sub(1, std::memory_order_relaxed);
    }
}

static void worker_trampoline(void* ctx, int worker_id) {
    SolverEngine<MAX_P>{}.run_worker(*static_cast<SolveJob*>(ctx), worker_id);
}

static int run_solve(
    const SerializedPuzzle& puzzle,
    const SimSchedule& sched,
    const std::vector<StartingConfig>& configs,
    SerializedSolution* out_solutions,
    int max_solutions,
    int num_threads
) {
    int pool_max = WorkStealingPool::get().max_threads();
    int n_workers = (num_threads <= 0) ? pool_max : std::min(num_threads, pool_max);
    if (n_workers <= 1) {
        SolverEngine<MAX_P> engine{};
        SolveJob job(&puzzle, &sched, &configs, out_solutions, max_solutions, 1);
        auto on_sol = [&](State& sol) { job.record_solution(sol); };
        YieldFn sol_yield = make_yield(on_sol);
        for (const auto& cfg : configs) {
            engine.world_check_with_sched(puzzle, sched, cfg, sol_yield, nullptr, 0);
        }
        return job.num_solutions;
    } else {
        SolveJob job(&puzzle, &sched, &configs, out_solutions, max_solutions, n_workers);
        WorkStealingPool::get().run_job(&job, &SolverEngine<MAX_P>::worker_trampoline, n_workers);
        return job.num_solutions;
    }
}

}; // struct SolverEngine

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

int solve_puzzle_cpp_mt(
    const clockchecker::SerializedPuzzle* puzzle_ptr,
    clockchecker::SerializedSolution* out_solutions,
    int max_solutions,
    int num_threads
) {
    using namespace clockchecker;
    const SerializedPuzzle& puzzle = *puzzle_ptr;
    g_current_puzzle = &puzzle;
    const int N = puzzle.num_players;

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
        for (int i = 0; i < N; ++i) {
            if (in_play[i] == CHAR_PitHag) pithag_in_play = true;
            if (in_play[i] == CHAR_FangGu) fanggu_in_play = true;
            if (in_play[i] == CHAR_Cerenovus) cerenovus_in_play = true;
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

    std::vector<StartingConfig> configs;
    configs.reserve(256);

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
                                configs.push_back(config);
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
                                            configs.push_back(extra_cfg);
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

    SimSchedule sched = build_schedule(puzzle);
    int num_solutions = 0;

    if (!configs.empty()) {
        if (N <= 8) {
            num_solutions = SolverEngine<8>::run_solve(puzzle, sched, configs, out_solutions, max_solutions, num_threads);
        } else if (N <= 9) {
            num_solutions = SolverEngine<9>::run_solve(puzzle, sched, configs, out_solutions, max_solutions, num_threads);
        } else if (N <= 12) {
            num_solutions = SolverEngine<12>::run_solve(puzzle, sched, configs, out_solutions, max_solutions, num_threads);
        } else {
            num_solutions = SolverEngine<16>::run_solve(puzzle, sched, configs, out_solutions, max_solutions, num_threads);
        }
    }

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
                sp.ceremad = 0;
                sp.vigormortised = 0;
                sp.self_droison = 0;
                sp.target = NONE_PLAYER;
                sp.aux_target = NONE_PLAYER;
                sp.history_len = 0;
                sp.char_history_len = 0;
            }
        }
    }

    return num_solutions;
}

int solve_puzzle_cpp(
    const clockchecker::SerializedPuzzle* puzzle_ptr,
    clockchecker::SerializedSolution* out_solutions,
    int max_solutions
) {
    return solve_puzzle_cpp_mt(puzzle_ptr, out_solutions, max_solutions, 0);
}

int get_serialized_puzzle_size() {
    return static_cast<int>(sizeof(clockchecker::SerializedPuzzle));
}

int get_serialized_solution_size() {
    return static_cast<int>(sizeof(clockchecker::SerializedSolution));
}

} // extern "C"
