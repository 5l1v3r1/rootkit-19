import datetime
import random
import uuid


class Game(object):
    def __init__(self):
        self.players = []
        self.uuid = uuid.uuid4()

    def _get_other_players(self, player):
        return [p for p in self.players if p.index != player.index]

    def add_player(self, player):
        self.players.append(player)
        player.index = len(self.players) - 1

    def set_command(self, server, turn):
        server.set_command(turn)

    def dump(self):
        print "-----------------------------------------------"
        for player in self.players:
            player.dump()

    def resolve(self):
        # Resolution is done in two phases:
        # Pre-cycle - fast operations, take effect immediately
        # Post-cycle - slow operations, takes a full cycle
        try:
            for player in self.players:
                for s in player.servers:
                    cmd = s.current_cmd
                    pre_result = "noop"
                    if cmd:
                        other_players = self._get_other_players(player)
                        pre_result = cmd.pre_cycle(s, player, other_players)
                    s.pre_result = pre_result

            for player in self.players:
                for s in player.servers:
                    cmd = s.current_cmd
                    post_result = "noop"
                    if cmd:
                        other_players = self._get_other_players(player)
                        result = cmd.post_cycle(s, player, other_players)
                        cmd.duration -= 1
                        if cmd.duration < 0:
                            result = s.current_cmd.completed(
                                                s, player, other_players)
                            s.current_cmd = None
                    s.post_result = result
        except BadCommand as e:
            s.post_result = "Error: %s" % str(e)
            s.current_cmd = None


class Weakness(object):
    def __init__(self, description):
        self.description = description
        self.found_by = []

    def __str__(self):
        return self.description


class Server(object):
    def __init__(self):
        self.ip = "%d.%d.%d.%d" % tuple(
                        [random.randrange(255) for x in range(4)])
        # All servers start with a set of weaknesses.
        # They can be removed by Hardening a server.
        self.weaknesses = [Weakness('dictionary root password'),
                           Weakness('anonymous telnet'),
                           Weakness('missing patches'),
                           Weakness('SSL.v3')]
        self.current_cmd = None
        self.pre_result = None
        self.post_result = None

    def set_command(self, command):
        self.current_cmd = command

    def __str__(self):
        return str(self.ip)

    def dump(self, player):
        print "Server: %s" % self.ip
        for w in self.weaknesses:
            if player.index in w.found_by:
                print "    '%s' weakness" % w
        if self.pre_result:
            print "   > %s" % self.pre_result
        if self.post_result:
            print "   < %s" % self.post_result
        if self.current_cmd:
            print "    %d cycle(s) left" % self.current_cmd.duration


class Player(object):
    def __init__(self, handle):
        self.handle = handle
        self.index = -1  # Not added
        self.servers = [Server() for x in range(3)]
        self.known_servers = []
        self.credits = 1

    def dump(self):
        print "%s (%d): %d credits" % (self.handle, self.index, self.credits)
        for server in self.servers:
            print "   ",
            server.dump(self)
        if self.known_servers:
            print "    Known servers"
            for k in self.known_servers:
                print "   ",
                k.dump(self)

    def get_free_servers(self):
        return [s for s in self.servers if not s.current_cmd]

    def get_busy_servers(self):
        return [s for s in self.servers if s.current_cmd]


class Command(object):
    def __init__(self):
        self.when = datetime.datetime.utcnow()
        # Duration > 1 : still busy
        # Duration == 1 : time to do work
        # Duration == 0 : done
        self.duration = 0

    def pre_cycle(self, server, player, other_players):
        return "noop"

    def post_cycle(self, server, player, other_players):
        return "noop"

    def completed(self, server, player, other_players):
        return "noop"


class BadCommand(Exception):
    pass


class NMap(Command):
    def __init__(self, mask):
        super(NMap, self).__init__()
        self.mask = mask
        parts = self.mask.split(".")
        duration = 0
        path = []
        for p in parts:
            p = p.strip()
            if p == '*':
                duration += 1
                path.append(p)
            else:
                address = int(p)
                path.append(address)
        self.path = path
        self.duration = duration

    def pre_cycle(self, server, player, other_players):
        if len(self.path) != 4:
            self.duration = 0
            raise BadCommand("Invalid nmap mask given %s" % self.path)

        return "%s running 'nmap' against %s" % (
                        player.handle, self.path)

    def completed(self, server, player, other_players):
        choices = []
        for p in other_players:
            for s in p.servers:
                if s not in p.known_servers:
                    choices.append(s)
                    break
        hit = random.choice(choices)

        if not hit:
            return "%s completed 'nmap' against %s. " \
                   "No new servers found." % (
                   player.handle, self.path, hit)

        player.known_servers.append(hit)
        return "%s completed 'nmap' against %s. Found %s" % (
                player.handle, self.path, hit)


class Mine(Command):
    def execute(self, server, player, other_players):
        player.credits += 1
        self.duration = 1
        return "%s mined for 1 credit on %s" % (player.handle, server)


class Probe(Command):
    def __init__(self, target):
        self.target = target
        self.duration = 2

    def execute(self, server, player, other_players):
        # TODO(sandy): Duration should be based on the quality
        # of the tools you have.
        if self.duration > 1:
            return "Probing %s" % self.target
        if self.target.weaknesses:
            weakness = random.choice(self.target.weaknesses)
            if player.index in weakness.found_by:
                weakness = None
            else:
                weakness.found_by.append(player.index)
            if weakness:
                return "Found '%s' weakness on %s" % (weakness, self.target)

        return "No new weakness found on %s" % self.target


if __name__ == '__main__':
    game = Game()
    bob = Player("Bob")
    mary = Player("Mary")
    fred = Player("Fred")
    sue = Player("Sue")
    game.add_player(bob)
    game.add_player(mary)
    game.add_player(fred)
    game.add_player(sue)

    all_players = [bob, mary, fred, sue]
    for p in all_players:
        for s in p.get_free_servers():
            game.set_command(s, NMap("*.*.*.*"))

    game.dump()

    for x in range(4):
        game.resolve()
        game.dump()

    for p in all_players:
        for s in p.get_free_servers():
            game.set_command(s, Mine())
    game.resolve()
    game.dump()

    for p in all_players:
        for s in p.get_free_servers():
            game.set_command(s, Probe(p.known_servers[0]))
    for x in range(2):
        game.resolve()
        game.dump()

