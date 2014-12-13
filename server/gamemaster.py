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

    def set_command(self, player, turn):
        player.set_command(turn)

    def dump(self):
        print "-----------------------------------------------"
        for player in self.players:
            player.dump()

    def resolve(self):
        for player in self.players:
            cmd = player.current_cmd
            result = "No commands received from %s" % player.handle
            if cmd:
                other_players = self._get_other_players(player)
                result = cmd.execute(player, other_players)
                cmd.duration -= 1
                if cmd.duration < 0:
                    player.current_cmd = None
            player.last_result = result


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

    def __str__(self):
        return str(self.ip)

    def dump(self, player):
        print "Server: %s" % self.ip
        for w in self.weaknesses:
            if player.index in w.found_by:
                print "    '%s' weakness" % w


class Player(object):
    def __init__(self, handle):
        self.handle = handle
        self.index = -1  # Not added
        self.current_cmd = None
        self.servers = [Server()]
        self.known_servers = []
        self.is_free = True
        self.last_result = None
        self.credits = 1

    def set_command(self, command):
        self.current_cmd = command

    def dump(self):
        print "%s (%d): %d credits" % (self.handle, self.index, self.credits)
        if self.last_result:
            print "    %s" % self.last_result
        if self.current_cmd:
            print "    %d cycle(s) left" % self.current_cmd.duration
        for server in self.servers:
            print "   ",
            server.dump(self)
        if self.known_servers:
            print "    Known servers"
            for k in self.known_servers:
                print "   ",
                k.dump(self)

class Command(object):
    def __init__(self):
        self.when = datetime.datetime.utcnow()
        self.duration = 0


class NMap(Command):
    def __init__(self, mask):
        super(NMap, self).__init__()
        self.mask = mask
        self.path = None

    def execute(self, player, other_players):
        if not self.path:
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

        if len(self.path) != 4:
            self.duration = 0
            return "Invalid nmap mask given %s" % self.path

        if self.duration > 1:
            return "%s running 'nmap' against %s" % (
                            player.handle, self.path)

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
    def execute(self, player, other_players):
        player.credits += 1
        self.duration = 1
        return "%s mined for 1 credit" % (player.handle)


class Probe(Command):
    def __init__(self, server):
        self.server = server
        self.duration = 2

    def execute(self, player, other_players):
        # TODO(sandy): Duration should be based on the quality
        # of the tools you have.
        if self.duration > 1:
            return "Probing %s" % self.server
        if self.server.weaknesses:
            weakness = random.choice(self.server.weaknesses)
            if player.index in weakness.found_by:
                weakness = None
            else:
                weakness.found_by.append(player.index)
            if weakness:
                return "Found '%s' weakness on %s" % (weakness, self.server)

        return "No new weakness found on %s" % self.server


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
        game.set_command(p, NMap("*.*.*.*"))

    game.dump()

    for x in range(4):
        game.resolve()
        game.dump()

    for p in all_players:
        game.set_command(p, Mine())
    game.resolve()
    game.dump()

    for p in all_players:
        game.set_command(p, Probe(p.known_servers[0]))
    for x in range(2):
        game.resolve()
        game.dump()

