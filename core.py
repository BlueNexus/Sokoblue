### IMPORTS
import pygame, sys, random, time
from pygame.locals import *
from copy import *
from pathfinding.core.diagonal_movement import DiagonalMovement
from pathfinding.core.grid import Grid
from pathfinding.finder.a_star import AStarFinder
### END IMPORTS

### PYGAME CONSTANTS
pygame.init()
TileWidth = 32
TileHeight = 32
TileFloorHeight = 32
DISPLAYSURF = None
FPS = 30   
ImageDict = {'floor':pygame.image.load("Imgs/ground.gif"),
             'wall':pygame.image.load("Imgs/wall.gif"),
             'diamond':pygame.image.load("Imgs/diamond.gif"),
             'keeper':pygame.image.load("Imgs/keeper.gif"),
             'crate':pygame.image.load("Imgs/crate.gif"),
             'fulldiamond':pygame.image.load("Imgs/fulldiamond.gif")}

TileMapping = { '#':ImageDict['wall'],
                '.':ImageDict['floor'],
                'U':ImageDict['diamond'],
                'O':ImageDict['crate'],
                '@':ImageDict['keeper'],
                'V':ImageDict['fulldiamond']}
FPSClock = pygame.time.Clock()
Grey = (107,102,102)
#Grey = (152,148, 147)
Black = (0,0,0)
White       = (255,255,255)
BgColour    = Grey
TextColour  = White
myfont = pygame.font.SysFont("monospace", 15)
### END PYGAME CONSTANTS
    


class GameController():
    '''
    Unused class.
    '''
    map_controller = None
    level_no = 0

    def handle_input(self, com):
        pass

class MapController():
    '''
    Controls everything related to the map and the display of such.
    '''
    current_map = None #The currently loaded map
    all_maps = [] #All maps available to load
    moves = 0 #Current movecount

    def drawMap(self):
        '''
        params: None
        Outputs: MapSurf
        Generates a MapSurf from the current map
        '''
        mapSurfWidth = self.current_map.width * TileWidth
        mapSurfHeight = self.current_map.height * TileHeight
        mapSurf = pygame.Surface((mapSurfWidth, mapSurfHeight))
        mapSurf.fill(BgColour)
        for w in range(self.current_map.height):
            for h in range(self.current_map.width):
                thisTile = pygame.Rect((w * TileWidth, h * TileFloorHeight, TileWidth, TileHeight))
                if str(self.get_tile_by_coords(h,w)) in TileMapping:
                    baseTile = TileMapping[str(self.get_tile_by_coords(h,w))]
                mapSurf.blit(baseTile, thisTile)
        return mapSurf

    def load_map(self, mp):
        '''
        params: mp (Map)
        outputs: None
        Loads a specified map
        '''
        self.current_map = mp
        self.sync_player_loc()
        self.moves = 0
    
    def load_next_map(self):
        '''
        Params: None
        Outputs: None
        Loads the next queued map
        '''
        if(self.current_map and len(self.all_maps)):
            self.all_maps.pop(0)
        if(not(len(self.all_maps))):
            #No more maps to play
            print("You win the game!")
            sys.exit()
            return
        self.load_map(self.all_maps[0])

    def add_map_to_queue(self, mp):
        '''
        Params: mp (Map)
        Outputs: None
        Adds a map to the queue
        '''
        if(not(mp in self.all_maps)):
            self.all_maps.append(mp)

    def step(self, dx, dy, tile):
        '''
        Params: dx, dy, tile (int, int, Tile)
        Outputs: None
        Debug function. Moves an object without running collision checks
        '''
        print(tile)
        obj = tile.remove_from_tile()
        x, y = self.get_tile_coords(tile)
        self.current_map.tiles[x + dx][y + dy].add_to_tile(obj)

    def try_step(self, dx, dy, tile, allow_recurse = 1):
        '''
        Params: dx, dy, tile, allow_recuse (int, int, Tile, int)
        Outputs: valid
        Tries to move an object, running collision checks. Allows recursion if allow_recurse > 0
        '''
        valid = True
        self.moves += 1
        x, y = self.get_tile_coords(tile) 
        dest = self.current_map.tiles[x + dx][y + dy]
        if(len(dest.contents)): #Checking for boxes
            if(allow_recurse):
                valid = self.try_step(dx, dy, dest, allow_recurse - 1)
                if(valid):
                    self.moves -= 1
            else: #We can't push a box into a box or wall.
                self.moves -= 1
                valid = False
        if(not dest.obj_passable):
            #Trying to move into a wall
            valid = False
        if(valid):
            #Valid move, move us forward
            obj = tile.remove_from_tile()
            dest.add_to_tile(obj)
        self.check_map_completion()
        return valid

    def get_tile_coords(self, tile):
        '''
        Params: tile (Tile)
        Outputs: row, col (int, int)
        Gets the coordinates of a given tile
        '''
        for row in range(self.current_map.height):
            for col in range(self.current_map.width):
                if(self.current_map.tiles[row][col] == tile):
                    return row, col


    def get_obj_by_type(self, objtype):
        '''
        Params: objtype (Type)
        Outputs: i, col (Object, Tile)
        Searches the map for an object with the given type
        Returns that object and its tile
        '''
        for row in self.current_map.tiles:
            for col in row:
                for i in col.contents:
                    if(type(i) == objtype):
                        return i, col

    def check_map_completion(self):
        '''
        Params: None
        Outputs: None
        Checks if all diamonds on the map are full
        If they are, loads the next map
        '''
        valid = True
        completed = 0
        for to_check in self.get_all_tiles_by_type(Diamond):
            if(not to_check.check_full()):
                valid = False
            else:
                completed += 1
        if(valid):
            print("YOU WIN!")
            self.load_next_map()
        print("Boxes remaining: " + str(self.current_map.boxcount - completed))
        

    def get_all_tiles_by_type(self, tiletype):
        '''
    Params: tiletype (Type)
    Outpts: results (Array)
    Find all tiles of the specified type on the map, and return them
    '''
        results = []
        for row in self.current_map.tiles:
            for col in row:
                if(type(col) == tiletype):
                    results.append(col)
        return results

    def get_player_tile(self):
        '''
    Params: None
    Outputs: Tile
    Find the tile that the player is currently located in, and return it.
    '''
        self.sync_player_loc()
        return self.get_tile_by_coords(self.current_map.player.x_position, self.current_map.player.y_position)

    def get_tile_by_coords(self, x, y):
        '''
    Params: x, y (int, int)
    Outputs: tile
    Find the tile at the given x and y coordinates
    '''
        return self.current_map.tiles[y][x]

    def place_tile(self, x, y, tile):
        '''
    Params: x, y, tile (int, int, Tile)
    Outputs: None
    Places a tile at the given x and y coordinates
    '''
        self.current_map.tiles[x][y] = tile

    def sync_player_loc(self):
        '''
    Params: None
    Outputs: None
    Sets the player's internal x and y values to their actual values on the map.
    '''
        p, c = self.get_obj_by_type(Player)
        y, x = self.get_tile_coords(c)
        p.y_position, p.x_position = y, x


class Tile():
    '''
    Base tile object. Can contain objects.
    '''
    base_sprite = "."
    obj_passable = True
    player_passable = True
    can_hold_objects = True
    x = 0
    y = 0


    def __init__(self, nx, ny):
        self.sprite = self.base_sprite
        self.contents = []
        self.x = nx
        self.y = ny

    def add_to_tile(self, obj):
        '''Params: obj (Object)
    Outputs: obj or False (Object or Boolean)
    If this tile is empty, adds the object to its contents. Otherwise, return false
    '''
        if(obj not in self.contents and self.is_empty()):
            self.contents.append(obj)
            self.update_icon()
            return obj
        return False

    def is_empty(self):
        '''Params: None
        Outputs: True or False
        If this tile is empty, return true, otherwise false
        '''
        if(len(self.contents) == 0 and self.can_hold_objects):
            return True
        return False

    def remove_from_tile(self):
        '''
    Params: None
    Outputs: res (Object)
    Removes any objects in the tile, and returns them.
    '''
        if(len(self.contents) != 0):
            res = self.contents.pop(0)
            self.update_icon()
            return res

    def update_icon(self):
        '''
    Params: None
    Outputs: None
    Sets this tile's sprite to its content's sprite if available,
    or its base sprite otherwise.
    '''
        if((len(self.contents) != 0) and self.contents[0] is not None):
            self.sprite = self.contents[0].sprite if len(self.contents) != 0 else self.base_sprite
        else:
            self.sprite = self.base_sprite

    def get_obj_by_name(self, name):
        '''
    Params: name (String)
    Outputs: Object or Boolean
    '''
        if(len(self.contents) != 0):
            if(self.contents[0].name == name):
                return self.contents[0]
        return False

    def __str__(self):
        return self.sprite

class Wall(Tile):
    #An impassable wall tile'
    base_sprite = "#"
    player_passable = False
    obj_passable = False
    can_hold_objects = False

class Diamond(Tile):
    #A passable diamond tile, while you need to get crates onto.'
    base_sprite = "U"

    def __init__(self):
        self.sprite = self.base_sprite
        self.contents = []
        self.is_full = False

    def check_full(self):
        if(self.get_obj_by_name("Box")):
            self.is_full = True
        else:
            self.is_full = False
        return self.is_full

    def add_to_tile(self, obj):
        if(obj not in self.contents and len(self.contents) == 0 and self.can_hold_objects):
            self.contents.append(obj)
            self.update_icon()
            self.check_full()
            return obj
        return False
    
    def update_icon(self):
        if(len(self.contents) != 0):
            self.check_full()
            if(self.is_full):
                self.sprite = "V"
                return
            self.sprite = self.contents[0].sprite if len(self.contents) != 0 else self.base_sprite
        else:
            self.sprite = self.base_sprite

    def remove_from_tile(self):
        if(len(self.contents) != 0):
            res = self.contents.pop(0)
            self.update_icon()
            self.check_full()
            return res

class Box():
    #A box object
    sprite = "O"
    name = "Box"
    diamond = None

    def __init__(self, d):
        self.diamond = d

class Player():
    #A player object
    sprite = "@"
    name = "Player"

    def __init__(self, x, y):
        self.x_position = x
        self.y_position = y

class GameMap():
    #Base game map class, which RandomGameMap inherits from.
    tiles = []

    def __init__(self, h, w, b, s):
        self.height = 0
        self.width = 0
        self.boxcount = 0
        self.source = s
        #self.load_template(source)

class RandomGameMap(GameMap):
    #Randomised game map. This is where things get interesting.
    tiles = []
    waypoints = []

    def __init__(self, h, w, b, wc, d, ids):
        self.height = h
        self.width = w
        self.moves = 0
        self.boxcount = b
        self.wallcount = wc
        self.difficulty = d
        self.id = ids
        self.player = None
        self.generate()

    def get_line(self, x1, y1, x2, y2):
        '''
    Params: x1, y1, x2, y2 (int, int, int, int)
    returns: List of tiles
    Attempts to draw a random line, on the game map.
    '''
        res = []
        #Difference between the x and y coordinates
        diffx = x2 - x1
        diffy = y2 - y1
        #Total number of tiles to select
        steps = (abs(diffx) + abs(diffy))
        curx = x1
        cury = y1
        #Difference per x/y coordinate
        diffsx = diffx / steps
        diffsy = diffy / steps
        '''
        print("DEBUG START")
        print("X coordinate 1: " + str(x1))
        print("X coordinate 2: " + str(x2))
        print("Y coordinate 1: " + str(y1))
        print("Y coordinate 2: " + str(y2))
        print("X coordinate difference: " + str(diffx))
        print("Y coordinate difference: " + str(diffy))
        print("Total steps: " + str(steps))
        print("Current X coordinate: " + str(curx))
        print("Current Y coordinate: " + str(cury))
        print("X difference per step: " + str(diffsx))
        print("Y difference per step: " + str(diffsy))
   '''
        for it in range(steps):
            #print("Step " + str(it) + ": X coordinate: " + str(int(round(curx))))
            #print("Step " + str(it) + ": Y coordinate: " + str(int(round(cury))))
            curx += diffsx
            cury += diffsy
            res.append(self.tiles[int(round(cury))][int(round(curx))])
        #print("DEBUG END")
        return res

    def reject(self):
        #'This map is unsolveable, try again.
        print("REJECTING")
        self.tiles = None
        self.generate()
    
    def generate(self):
        #'Oh god here we go.
        #Generate the base map
        self.waypoints = []
        self.tiles = [[Tile(x,y) for x in range(self.width)] for y in range(self.height)]
        for row_no, row in enumerate(self.tiles):
            for col_no, col in enumerate(row):
                if(row_no == 0 or col_no == 0 or row_no == self.height - 1 or col_no == self.width - 1):
                    self.place_tile(row_no, col_no, Wall(row_no, col_no))

        #Draws random walls
        for wall in range(self.wallcount):
            valid = False
            rand1x = 0
            rand1y = 0
            rand2x = 0
            rand2y = 0
            while(valid == False):
                randx = random.randint(1, self.height - 1)
                randy = random.randint(1, self.width - 1)
                startpos = self.tiles[randx][randy]
                #Reuse the same variables, for effiency
                rand1x, rand1y = randx, randy
                randx = random.randint(1, self.height - 1)
                randy = random.randint(1, self.width - 1)
                endpos = self.tiles[randx][randy]
                rand2x, rand2y = randx, randy
                if(startpos == endpos):
                    continue
                valid = True
            path = self.get_line(rand1x, rand1y, rand2x, rand2y)
            for t in path:
                try:
                    x, y = t.x, t.y
                except:
                    #Something went wrong, CODE RED ABORT ABORT
                    self.reject()
                    return
                self.tiles[x][y] = Wall(x,y)

        #Place the player. Somewhere.
        valid = False
        playertile = None
        while(valid == False):
            playertile = self.tiles[random.randint(1, self.height -1)][random.randint(1, self.width - 1)]
            valid = playertile.add_to_tile(Player(1,1))
            self.player = valid
            random.seed()
        waypoints = [playertile]
        #tiles_to_check = [roaming_pos] #Tiles to attempt to pathfind between

        def makepath(tile):
            #print("STARTING PATH CALCULATION")
            start_point = tile
            line_length = self.difficulty
            startbox = Box(start_point)
            start_point.add_to_tile(startbox)
            step = 0
            path = [start_point]
            next_point = 0
            tries = 0
            #Move a box backwards, to make sure the game can be solved.
            while(step < line_length):
                #time.sleep(0.025)
                #print(str(self))
                tries += 1
                if(tries > self.difficulty * 10):
                    path[-1].remove_from_tile()
                    #OH GOD ABORT IT'S ALL ON FIRE
                    return False, False, False, False
                dx = 0
                dy = 0
                x_or_y = random.choice((1,2))
                if(x_or_y == 1):
                    dx = random.choice((1,-1))
                else:
                    dy = random.choice((1,-1))
                #print("STEP: " + str(step))
                try_add, next_tile = self.try_step(dx,dy,path[-1])
                if(try_add):
                    #print("PROGRESSING")
                    path.append(try_add)
                    step += 1
                else:
                    if(len(path) > 1):
                        #print("REGRESSING")
                        path[-2].add_to_tile(path[-1].remove_from_tile())
                        path.pop(-1)
                        step -= 1
            #print(str(self))
            
            
            return path, path[1], next_tile, startbox

        #Randomly place diamonds, then a box.
        for box in range(self.boxcount):
            tries = 0
            ovalid = False #I just realised that this looks like something else entirely
            while(ovalid == False):
                if(tries > self.boxcount * 6):
                    #As usual, it's all gone wrong oh god send the fire brigade
                    #Seriously though, this is here to prevent an infinite loop.
                    self.reject()
                    return False
                valid = False
                randx = 0
                randy = 0
                while(valid == False):
                    randx = random.randint(1, self.height-1)
                    randy = random.randint(1, self.width-1)
                    if(not(len(self.tiles[randx][randy].contents)) and (self.tiles[randx][randy].can_hold_objects)):
                        self.tiles[randx][randy] = Diamond()
                        valid = True
                    random.seed()
                path, endpoint, startpoint, temp_box = makepath(self.get_tile(randx,randy))
                if(path):
                    waypoints.append(startpoint)
                    waypoints.append(endpoint)
                    #tiles_to_check.append([box_end_pos, temp_box])
                    ovalid = True
                else:
                    tries += 1
                    self.tiles[randx][randy] = Tile(randx, randy)

        #Try and make sure the level can be solved. Emphasis on try.
        check_box_count = 0
        check_diamond_count = 0
        for l in range(self.height):
            for r in range(self.width):
                if(len(self.tiles[l][r].contents)):
                    if(type(self.tiles[l][r].contents[0]) == Box):
                        '''
                        if((self.is_not_passable(l+1, r) and self.is_not_passable(l, r+1))\
                           or (self.is_not_passable(l+1, r) and self.is_not_passable(l, r-1))\
                           or (self.is_not_passable(l-1, r) and self.is_not_passable(l, r+1))\
                           or (self.is_not_passable(l-1, r) and self.is_not_passable(l, r-1))):
                            

                            self.reject()
    
                            return
                        '''
                        check_box_count += 1
                if(type(self.tiles[l][r]) == Diamond):
                    check_diamond_count += 1
        if(not(check_box_count == check_diamond_count)):
            #We somehow generated too many boxes, abort.
            self.reject()
            return

        #Create a grid out of the tiles 2d array
        resgrid = Grid(matrix=self.convert_to_grid(self.tiles))
        finder = AStarFinder(diagonal_movement = DiagonalMovement.never)

        #Create a copy of the waypoints list and remove any errored waypoints
        for point in waypoints[:]:
            print("X: ", point.x, "Y:", point.y)
            if(point.x == 0 and point.y == 0):
                print("oops")
                waypoints.remove(point)
        
        def get_node(to_node):
            coordx, coordy = to_node.x, to_node.y
            return resgrid.node(coordx, coordy)

        #Turn the waypoints list into a list of nodes
        nodes = []
        for pos in range(len(waypoints)):
            nodes.append(get_node(waypoints[pos]))

        '''
        path, runs = finder.find_path(playerpos, nodes[0], resgrid)
        if(len(path) == 0):
            self.reject()
            return 
        print("operations",runs,"path length:", len(path))
        '''

        for node_index in range(len(nodes)):
            if(node_index + 1 <= len(nodes)-1):
                resgrid.cleanup()

                path, runs = finder.find_path(nodes[node_index], nodes[node_index + 1], resgrid)
                print(resgrid.grid_str(path=path, start=nodes[node_index], end=nodes[node_index + 1]))
                print("operations",runs,"path length:", len(path))

                if(len(path) == 0):
                    self.reject()
                    return
        

    


    def convert_to_grid(self, to_grid):
        results = [];
        temp = [];
        for indexh in range(self.height):
            temp = [];
            for indexw in range(self.width):
                char = str(to_grid[indexh][indexw])
                conv_char = "0" if char in ["#"] else "1"
                temp.append(conv_char)
            results.append(temp)
            print(temp)
        return results
            

    #deprecated
    def get_tile_coords(self, tile):
        for row in range(self.height):
            for col in range(self.width):
                if(self.tiles[row][col] == tile):
                    return row, col

    def try_step(self, dx, dy, tile):
        valid = True
        x, y = self.get_tile_coords(tile)
        try:
            dest = self.tiles[x + dx][y + dy]
        except:
            valid = False
            return valid, valid
        if(len(dest.contents)):
            valid = False
            return valid, valid
        if(not dest.obj_passable):
            valid = False
            return valid, valid
        next_tile = self.tiles[x + (dx*2)][y + (dy*2)]
        try:
            if(not next_tile.is_empty()):
                valid = False
                return valid, valid
        except:
            valid = False
            return valid, valid
        if(valid):
            obj = tile.remove_from_tile()
            dest.add_to_tile(obj)
            return dest, next_tile
        return False

    def is_not_passable(self, x, y):
        if((0 < x < self.width - 1) and 0 < y < self.height - 1):
            return(len(self.get_tile(x,y).contents))
        return False
    
    '''
    def check_box_pos_validity(self, pos):
        x, y = self.get_tile_coords(pos)
        print(str(self.get_tile(x, y)))
        if(self.is_not_passable(x, y)):
            print("Target tile is not passable")
            return False
        if((self.is_not_passable(x+1, y) and self.is_not_passable(x, y+1))\
           or (self.is_not_passable(x+1, y) and self.is_not_passable(x, y-1))\
           or (self.is_not_passable(x-1, y) and self.is_not_passable(x, y+1))\
           or (self.is_not_passable(x-1, y) and self.is_not_passable(x, y-1))):
            print("Corner tiles aren't passable")
            return False
        if(type(self.get_tile(x,y)) == Diamond):
            print("Cannot place on diamond")
            return False
        return True


    '''

    def get_tile(self, x, y):
        return self.tiles[x][y]

    def place_tile(self, x, y, tile):
        self.tiles[x][y] = tile

    def __str__(self):
        result = ""
        count = 0
        for ti in self.tiles:
            for su in ti:
                count += 1
                result += (str(su) if (not count % self.width == 0) else str(su) + "\n")
        return(result.replace("[]',", ""))
            
def move(char):
    x = 0
    y = 0
    if(char == "w"):
        x = -1
    if(char == "a"):
        y = -1
    if(char == "s"):
        x = 1
    if(char == "d"):
        y = 1
    if(char == "r"):
        return "Restart"
    mc.try_step(x, y, mc.get_player_tile())

mc = MapController()

def loadMapDisplay(half):
    global DISPLAYSURF
    mapSurf = pygame.Surface((half*2, half*2))
    pygame.display.get_surface().fill(BgColour)
    mapSurf.fill(BgColour)
    mapSurf = mc.drawMap()
    mapSurfRect = mapSurf.get_rect()
    mapSurfRect.center = (half, half)
    DISPLAYSURF.blit(mapSurf, mapSurfRect)
    label = myfont.render(str(mc.moves), 1, (255,255,255))
    DISPLAYSURF.blit(label, (0, 0))
    pygame.display.update()
    FPSClock.tick()

def main():
    global DISPLAYSURF

    valid = False
    mp = None
    levelcount = int(input("Please enter the total number of levels."))
    screensize = 32 * (10 + round(levelcount * 1.25))
    print(screensize)
    DISPLAYSURF = pygame.display.set_mode((screensize, screensize))
    for i in range(levelcount):
        valid = False
        while(valid == False):
            pygame.event.get()
            mp = RandomGameMap(round(10+(i*1.15)),round(10+(i*1.15)),5+i*3,round(3+(i*0.75)),14+(i*5),i)
            print(str(mp))
            mc.load_map(mp)
            loadMapDisplay(screensize/2)
            v = int(input("Please enter 1 if there are no crates, boxes or players in blocked-off sections on this level, and that all boxes are accessible, otherwise 0"))
            if(v == 1):
                valid = True
        mc.add_map_to_queue(mp)

    mc.load_next_map()
    mapcopy = deepcopy(mc.current_map)
    while(True):
        loadMapDisplay(screensize/2)

        if(mapcopy.id != mc.current_map.id):
            mapcopy = deepcopy(mc.current_map)
        print("Moves: " + str(mc.moves))
        print(str(mc.current_map))
        for event in pygame.event.get():
            if event.type == KEYDOWN:
                if event.key == K_RIGHT or event.key == K_d:
                    move("s")
                elif event.key == K_UP or event.key == K_w:
                    move("a")
                elif event.key == K_LEFT or event.key == K_a:
                    move("w")
                elif event.key == K_DOWN or event.key == K_s:
                    move("d")
                elif event.key == K_SPACE:
                    mc.load_map(deepcopy(mapcopy))
                elif event.key == K_r:
                    main()
                    return
                else:
                    pass
                break
        #if(move(input(">>")) == "Restart"):
            #mc.load_map(deepcopy(mapcopy))

'''
#mp = RandomGameMap(50,50,100,7,14)
mp = RandomGameMap(10, 10, 5, 3, 14)
print(str(mp))
mc = MapController()
mc.load_map(mp)
print(str(mp))
'''
main()
