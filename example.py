import multiprocessing

from clockchecker import *


if __name__ == '__main__':
    # In case your OS is whack.
    multiprocessing.freeze_support()
    multiprocessing.set_start_method('spawn')


    Eevee, Amy, Ethan, Barrow, Lyra, JC, Emerald, Sincerity = range(8)
    puzzle = Puzzle(
        players=[
            Player('Eevee', claim=Seamstress, night_info={
                2: Seamstress.Ping(Emerald, Amy, same=False),
            }),
            Player('Amy', claim=Dreamer, night_info={
                1: Dreamer.Ping(Eevee, Seamstress, Vigormortis),
                2: Dreamer.Ping(JC, Oracle, NoDashii),
                3: Dreamer.Ping(Lyra, Sage, Vigormortis),
            }),
            Player('Ethan', claim=SnakeCharmer, night_info={
                1: SnakeCharmer.Choice(Barrow),
            }),
            Player('Barrow', claim=Artist, day_info={
                # 1: Artist.Ping(IsCharacter(Louisa, Drunk))
            }),
            Player('Lyra', claim=Sage, night_info={
                3: Sage.Ping(Amy, Eevee),
            }),
            Player('JC', claim=Oracle, night_info={
                2: Oracle.Ping(1),
                3: Oracle.Ping(1),
            }),
            Player('Emerald', claim=Clockmaker, night_info={
                1: Clockmaker.Ping(2)
            }),
            Player('Sincerity', claim=Mathematician, night_info={
                1: Mathematician.Ping(0),
                2: Mathematician.Ping(0),
            }),
        ],
        day_events={
            1: Execution(Ethan),
            2: Execution(Sincerity),
            3: Dies(player=JC, after_nominating=True),
        },
        night_deaths={2: Barrow, 3: Lyra},
        hidden_characters=[Vigormortis, NoDashii, Vortox, Witch, Mutant],
        hidden_self=[],
        player_zero_is_you=False,
    )

    print(puzzle, '\n\nSolving...\n')
    count = 0
    for world in solve(puzzle):
        if any(
            isinstance(p.character, Mutant) and p.is_dead
            for p in world.players
        ): 
            continue
        print(world)
        count += 1
    print(f'Found {count} worlds')