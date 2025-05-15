import multiprocessing

from clockchecker import *


if __name__ == '__main__':
    # In case your OS is whack.
    multiprocessing.freeze_support()
    multiprocessing.set_start_method('spawn')

    # https://discord.com/channels/569683781800296501/854891541969109033/1367073812063191081

    You, Sarah, Hannah, Jasmine, Josh, Dan, Aoife, Fraser = range(8)
    puzzle = Puzzle(
        players=[
            Player('You', claim=Empath, night_info={
                1: Empath.Ping(0),
            }),
            Player('Sarah', claim=Clockmaker, night_info={
                1: Clockmaker.Ping(3)
            }),
            Player('Hannah', claim=Philosopher, night_info={
                1: [
                    Philosopher.Choice(Chambermaid),
                    Chambermaid.Ping(Aoife, Fraser, 1),
                ],
                2: Chambermaid.Ping(Josh, Fraser, 2),
            }),
            Player('Jasmine', claim=Juggler,
                day_info={1: Juggler.Juggle({Hannah: Vortox, Josh: NoDashii})},
                night_info={2: Juggler.Ping(2)}
            ),
            Player('Josh', claim=Chef, night_info={
                1: Chef.Ping(1)
            }),
            Player('Dan', claim=Mathematician, night_info={
                1: Mathematician.Ping(2),
                2: Mathematician.Ping(1),
            }),
            Player('Aoife', claim=Chambermaid, night_info={
                1: Chambermaid.Ping(Hannah, Josh, 2),
            }),
            Player('Fraser', claim=Oracle, night_info={
                2: Oracle.Ping(2)
            }),
        ],
        day_events={1: [
            Dies(player=You, after_nominating=True),
            Execution(Aoife),
        ]},
        night_deaths={2: Sarah},
        hidden_characters=[NoDashii, Vortox, Witch, Drunk],
        hidden_self=[Drunk],
    )

    print(puzzle, '\n\nSolving...\n')

    solution1 = (Empath, Clockmaker, Philosopher, Juggler, Chef, 
                  Vortox, Drunk, Witch)
    solution2 = (Empath, Clockmaker, Philosopher, NoDashii, Chef, 
                  Mathematician, Witch, Drunk)

    for world in Solver().generate_worlds(puzzle):
        print('Found', world)
