import pygame
import sys
from abc import ABC, abstractmethod
import random
import json

class Screen(ABC):
    @abstractmethod
    def draw_screen(self):
        pass

    def draw_menu_boxes(self, menu_dict,
                        event_state,
                        item_name):
        container_cords = event_state.get_container_coords()
        width = menu_dict['box_dims']['width']
        height = menu_dict['box_dims']['height']
        x, y, width, height = calculate_menu_boxes\
            (menu_dict['coords'][item_name],
                                    container_cords, width, height)
        
        return x, y, width, height
    
    def get_title_coords(self, title_coords, event_state):
        x_off, y_off = title_coords['x_off'], title_coords['y_off']
        container_cords = event_state.get_container_coords()
        title_dims = calculate_title_coords(container_cords['cont_x'],
                                            container_cords['cont_y'],
                                            container_cords['cont_width'],
                                            container_cords['cont_height'],
                                            x_off, y_off)
        return title_dims
    
class Shape:
    def __init__(self, constants,
                event_state,screen,
                shape, shape_name, block_color,
                coords, curr_grid_col
                ):
        self.constants = constants
        self.event_state = event_state
        self.shape_rotation = shape
        self.screen = screen
        self.current_rotation = 0
        self.block_color = block_color
        self.shape_name = shape_name
        self.coords = coords
        self.all_rects = None
        self.current_grid_row = 0
        self.current_grid_col = curr_grid_col
      
    def increment_current_rotation(self):
        new_rot = self.current_rotation + 1
        shape = self.shape_rotation[self.shape_name][new_rot%4]
        BLOCK_SIZE = self.constants['BLOCK_SIZE']
        x, y = self.coords
        self._create_block_rects(shape, x, y, BLOCK_SIZE)
        locs = self._get_shape_block_idx()
        grid_cells = self.event_state.get_grid_matrix()
        for loc in locs:
            row = loc['row']
            col = loc['col']
            if (row < len(grid_cells)) and \
                (col < len(grid_cells[0])) and \
                    (grid_cells[row][col]['val'] == 1):
                return
            if row >= len(grid_cells):
                return
        self.current_rotation += 1

    def _create_block_rects(self, shape,
                            x, y,
                            BLOCK_SIZE,
                            draw=False,
                            BLACK=None):
        all_rects = []
        for row_index, row in enumerate(shape):
            for col_index, block in enumerate(row):
                if block == 1:
                    if draw:
                        pygame.draw.rect(self.screen, self.block_color, 
                                     (x + col_index * BLOCK_SIZE,
                                       y + row_index * BLOCK_SIZE,
                                         BLOCK_SIZE, BLOCK_SIZE))
                        pygame.draw.rect(self.screen, BLACK, 
                                        (x + col_index * BLOCK_SIZE, 
                                          y + row_index * BLOCK_SIZE,
                                            BLOCK_SIZE, BLOCK_SIZE), 1)
                    all_rects.append(
                        pygame.Rect(x + col_index * BLOCK_SIZE,
                                    y + row_index * BLOCK_SIZE,
                                    BLOCK_SIZE, BLOCK_SIZE)
                    )
        self.all_rects = all_rects

    def _adjust_rotation(self, shape, x, y, BLOCK_SIZE):
        self._create_block_rects(shape, x, y, BLOCK_SIZE)
        grid_cells = self.event_state.get_grid_matrix()
        
        x_blocks, _ = get_x_y_block_count(self)
        hold_blocks = self.constants['GRID_BLOCKS'][1] - \
                      self.current_grid_col
        if x_blocks > hold_blocks:
            b_diff = (x_blocks-hold_blocks)
            self.current_grid_col -= b_diff
            cell = grid_cells[self.current_grid_row][self.current_grid_col]
            x_coord = cell['coords']['x']
            self.coords[0] = x_coord
        
        self.all_rects = []

    def draw_shape(self, shape=None, BLACK=None,
                   BLOCK_SIZE=None, x=None, y=None):
        if shape is None:
          shape = self.shape_rotation[self.shape_name][self.current_rotation%4]
          BLACK = self.shape_rotation['BLACK']
          BLOCK_SIZE = self.constants['BLOCK_SIZE']
          x, y = self.coords

        self._adjust_rotation(shape, x, y, BLOCK_SIZE)

        self._create_block_rects(shape, x, y, BLOCK_SIZE, True, BLACK)
    
    def display_shape_in_next(self, y_off):
        shape = self.shape_rotation[self.shape_name][0]
        BLACK = self.shape_rotation['BLACK']
        BLOCK_SIZE = self.constants['BLOCK_SIZE']//2
        state = self.event_state.get_event_state()
        rects = self.event_state.get_menu_rectangles()
        rects = rects[state]
        rects = [x for x in rects if x['name']=="NEXT_SHAPE_CONTAINER"][0]['rect']
        cont_x, cont_y = rects.x, rects.y
        cont_width, cont_height = rects.width, rects.height
        x_off = 0.3
        x, y = place_items_at_offset_percent(cont_x,
                                             cont_y,
                                             cont_width,
                                             cont_height,
                                             x_off,
                                             y_off)
        self.draw_shape(shape=shape, BLACK=BLACK,
                        BLOCK_SIZE=BLOCK_SIZE,
                        x=x, y=y)
        
    def _get_shape_block_idx(self):
        block_size = self.constants['BLOCK_SIZE']
        locs = []
        for rect in self.all_rects:
            gx, gy, _, _ = self.event_state.get_game_grid_coords()
            x_loc = (rect.x - gx)//block_size
            y_loc = ((rect.y - gy)//block_size)+2
            locs.append({"row":y_loc, 'col':x_loc})
        return locs
    
    def _is_block_collided_down(self, grid_cells):
        shape_block_locs = self._get_shape_block_idx()
        for loc in shape_block_locs:
            row = loc['row']
            col = loc['col']
            if row + 1 < len(grid_cells):
                next_row = row+1
                if col < len(grid_cells[0]) and \
                  grid_cells[next_row][col]['val'] == 1:
                    return False
        return True
    
    def _is_block_collided_horiz(self, grid_cells):
        shape_block_locs = self._get_shape_block_idx()
        left_move, right_move = True, True
        for loc in shape_block_locs:
            row = loc['row']
            col = loc['col']
            prev_col = col - 1
            next_col = col + 1
            if prev_col >= 0:
                if grid_cells[row][prev_col]['val'] == 1:
                    left_move = False
            if next_col < len(grid_cells[0]):
                if grid_cells[row][next_col]['val'] == 1:
                    right_move = False
        return left_move, right_move
        
    def _fill_grid_matrix(self, grid_cells):
        locs = self._get_shape_block_idx()
        for loc in locs:
          x_loc, y_loc = loc['col'], loc['row']
          grid_cells[y_loc][x_loc]['val'] = 1
          grid_cells[y_loc][x_loc]['color'] = self.block_color
            
        self.event_state.set_grid_matrix(grid_cells)

    def _add_shape_to_existing(self, 
                               event_state,
                               elapsed_seconds,
                               movement_delay,
                               current_shape,
                               grid_cells):
        self._fill_grid_matrix(grid_cells)
        event_state.set_prev_movement(elapsed_seconds-movement_delay)
        event_state.set_current_shape(-1)
        event_state.set_existing_shapes(current_shape)
        score_calculator(self.event_state, self.constants)
        
    def move_shape_down(self, grid_cells):
      event_state = self.event_state
      elapsed_seconds = event_state.get_elapsed_seconds()
      movement_delay = event_state.get_movement_delay()
      prev_movement = event_state.get_prev_movement()
      is_block = self._is_block_collided_down(grid_cells)
      if(elapsed_seconds - prev_movement) >= movement_delay:
          self.current_grid_row += 1
          _, y_blocks = get_x_y_block_count(self)
          
          if (self.current_grid_row + y_blocks <= len(grid_cells)) and is_block:
            self.coords[1] =\
                grid_cells[self.current_grid_row]\
                  [self.current_grid_col]['coords']['y']
            event_state.set_prev_movement(elapsed_seconds)
          else:
              self._add_shape_to_existing(event_state, elapsed_seconds,
                                          movement_delay, self, grid_cells)
    
    def move_shape_horizontal(self, grid_cells):
        event_state = self.event_state
        elapsed_seconds = event_state.get_elapsed_seconds()
        movement_delay = event_state.get_horiz_delay()
        prev_movement = event_state.get_prev_horiz_movement()
        if (elapsed_seconds - prev_movement) < movement_delay:
          return
        x_blocks, _ = get_x_y_block_count(self)
        left_move, right_move = self._is_block_collided_horiz(grid_cells)
        if event_state.get_left_pressed() and left_move:
            if self.current_grid_col > 0:
                self.current_grid_col -= 1
                self.coords[0] = grid_cells[self.current_grid_row]\
                                  [self.current_grid_col]['coords']['x']

        elif event_state.get_right_pressed() and right_move:
            if (self.current_grid_col + x_blocks) < len(grid_cells[0]):
                self.current_grid_col += 1
                self.coords[0] = grid_cells[self.current_grid_row]\
                                  [self.current_grid_col]['coords']['x']
        event_state.set_prev_horiz_movement(elapsed_seconds)

class GridMatrix:
    def __init__(self, constants, event_state):
        self.constants = constants
        self.event_state = event_state

    def _create_grid(self, rows, cols, 
                    start_point_x, start_point_y,
                    block_size):
        grid_cells = []
        for _ in range(rows):
            grid_row = []
            sp_x = start_point_x
            for _ in range(cols):
                grid_row.append({"val":-1,
                                 "coords":{'x':sp_x,
                                           'y':start_point_y}})
                sp_x += block_size
            start_point_y += block_size
            grid_cells.append(grid_row)
        return grid_cells

    def load_grid(self):
        rows, cols = self.constants['GRID_BLOCKS']
        grid_coords = self.event_state.get_game_grid_coords()
        block_size = self.constants['BLOCK_SIZE']
        start_point_y = grid_coords[1] - (2 * block_size)
        start_point_x = grid_coords[0]
        rows += 2
        grid_cells = self._create_grid(rows, cols,
                                       start_point_x,
                                       start_point_y,
                                       block_size)
        self.event_state.set_grid_matrix(grid_cells)
        

class BagOfSeven:
    def __init__(self, 
                 constants, 
                 event_state,
                 screen,
                 shapes,
                 container_coords):
        self.constants = constants
        self.shape_rotations = shapes
        self.queue = []
        self.seven = []
        self.event_state = event_state
        self.screen = screen
        self.container_coords = container_coords

    def load_seven(self, grid_row):
        for k, v in self.shape_rotations.items():
            if k == "BLACK":
                continue
            random_color = random.choice(self.constants['RANDOM_COLORS'])
            block_size = self.constants['BLOCK_SIZE']
            random_pos = calculate_shape_pos(grid_row, k)
            blit_coords = [random_pos[0], random_pos[1]]
            shape_obj = Shape(self.constants,
                              self.event_state,
                              self.screen,
                              self.shape_rotations,
                              k,
                              random_color,
                              blit_coords,
                              random_pos[2]
                              )
            self.seven.append(shape_obj)
        self.seven  = random.sample(self.seven, len(self.seven))
    
    def append_queue(self):
        if len(self.queue) == 0:
            for x in range(0, 3):
                self.queue.append(self.seven[x])
            del self.seven[0: 3]
            return
        self.queue.append(self.seven[0])
        del self.seven[0]

    def get_queue_element(self):
        element = self.queue[0]
        del self.queue[0]
        self.append_queue()
        return element

class GameOver(Screen):
    def __init__(self, event_state,constants, screen, game):
        self.constants = constants
        self.event_state = event_state
        self.screen = screen
        self.game = game
        self.rectangles = []

    def blit_game_over(self, grid_coords, font, color):
        cx, cy = grid_coords['cont_x'], grid_coords['cont_y']
        cw, ch = grid_coords['cont_width'], grid_coords['cont_height']
        x_off = self.game['game_over_text']['x_off']
        y_off = self.game['game_over_text']['y_off']
        x, y = place_items_at_offset_percent(cx, cy,
                                             cw, ch,
                                             x_off, y_off)
        text_surface = font.render('GAME OVER', True, color)
        self.screen.blit(text_surface, (x, y))

    def blit_buttons(self, grid_coords, font, color,
                     button_name,
                     button_text):
        menu = self.game[button_name]
        box_dims = self.game['box_dims']
        x, y, width, height = calculate_menu_boxes(menu, grid_coords,
                                                    box_dims['width'], 
                                                    box_dims['height'])
        pygame.draw.rect(self.screen, color,
                            (x, y, width, height),
                            width=self.game['box_line_width'])
        text_surface = font.render(button_text, True, color)
        name_coords = center_elements(x, y, width, height,
                                        text_surface.get_width(),
                                        text_surface.get_height())
        self.screen.blit(text_surface, name_coords)
        self.rectangles.append({"rect":pygame.Rect(x, y, width, height),
                               "name":button_name})
        self.event_state.set_menu_rectangles(self.rectangles,
                                                self.event_state.get_event_state())

    def blit_highscore(self):
        pass

    def blit_enter_high_score_name(self):
        pass

    def blit_check_highscore(self):
        pass

    def draw_screen(self):
        grid_coords = self.event_state.get_container_coords()
        color = self.game['font_color']
        font = self.event_state.get_all_fonts()['text_font']
        self.blit_game_over(grid_coords, font, color)
        self.blit_buttons(grid_coords, font, color,
                          'play_again',
                          'Play Again')
        self.blit_buttons(grid_coords, font, color,
                          'exit',
                          'Exit')
        
class GameScreenScreen(Screen):
    def __init__(self, constants, title, game, event_state, screen,
                 ):
        self.constants = constants
        self.title = title
        self.game = game
        self.event_state = event_state
        self.screen = screen
        self.coords = self.event_state.get_container_coords()
        self.rectangles = []
        self.rectangle_menu_set = False

    def load_shape_objects(self):
        shapes_file = self.constants['shapes']
        shapes_dict = read_json(shapes_file)
        state = self.event_state.get_event_state()
        coords = self.event_state.get_menu_rectangles()[state] #GAME_GRID
        grid_coords = [x['rect'] for x in coords if x['name']=="GAME_GRID"][0]
        grid_coords = [grid_coords.x, grid_coords.y,
                       grid_coords.width,
                       grid_coords.height]
        bag_of_seven = BagOfSeven(self.constants,
                                  self.event_state,
                                  self.screen,
                                  shapes_dict,
                                  grid_coords)
        self.event_state.set_bag_of_7(bag_of_seven)
        return bag_of_seven

    def scores_blit(self, font, color):
        scoring_title = self.game["score_title"]
        scoring = self.game['score']
        score_title_coords = place_items_at_offset_percent(self.coords['cont_x']
                                                    ,self.coords['cont_y']
                                                    ,self.coords['cont_width'],
                                                    self.coords['cont_height'],
                                                    scoring_title['x_off'],
                                                    scoring_title['y_off'])
        score_coords = place_items_at_offset_percent(self.coords['cont_x']
                                                    ,self.coords['cont_y']
                                                    ,self.coords['cont_width'],
                                                    self.coords['cont_height'],
                                                    scoring['x_off'],
                                                    scoring['y_off'])
        score = self.event_state.get_score()
        text_surface = font.render('SCORE', True, color)
        score_surface = font.render(str(score), True, color)
        self.screen.blit(text_surface, score_title_coords)
        self.screen.blit(score_surface, score_coords)

    def grid_blit(self, grid_boundary_color, block_size):
        rows, cols = self.game['rows'], self.game['cols']
        grid_dims = calculate_grid_dims(self.coords['cont_x']
                                        ,self.coords['cont_y']
                                        ,self.coords['cont_width'],
                                        self.coords['cont_height'],
                                        block_size, rows, cols
                                        )
        x, y, width, height = grid_dims
        pygame.draw.rect(self.screen, grid_boundary_color,
                         (x-1, y-1, width+1, height+1),
                         width=1)
        self.rectangles.append({"rect":pygame.Rect(x-1, y-1, width+1, height+1),
                               "name":'GAME_GRID'})
        self.event_state.set_game_grid_coords([x, y, width, height])
        
    def grid_exit_blit(self, color, font):
        self.game['coords'] = {}
        self.game['coords']['EXIT'] = self.game['exit']
        x, y, width, height = self.draw_menu_boxes(self.game,
                                                    self.event_state, 'EXIT')
        pygame.draw.rect(self.screen, color,
                            (x, y, width, height),
                            width=self.game['box_line_width'])
        self.rectangles.append({"rect":pygame.Rect(x, y, width, height),
                               "name":'EXIT'})
        text_surface = font.render('EXIT', True, color)
        name_coords = center_elements(x, y, width, height,
                                        text_surface.get_width(),
                                        text_surface.get_height())
        self.screen.blit(text_surface, name_coords)
        
    def shape_blit(self, color, block_size, font):
        next_shapes_container = self.game['next_shapes_container']
        rows, cols = 8, 8
        x, y = place_items_at_offset_percent(self.coords['cont_x']
                                    ,self.coords['cont_y']
                                    ,self.coords['cont_width'],
                                    self.coords['cont_height'],
                                    next_shapes_container['x_off'],
                                    next_shapes_container['y_off'])
        width = block_size * rows
        height = block_size * cols

        next_shapes = self.game['next_shapes']
        x_t, y_t = place_items_at_offset_percent(self.coords['cont_x']
                                ,self.coords['cont_y']
                                ,self.coords['cont_width'],
                                self.coords['cont_height'],
                                next_shapes['x_off'],
                                next_shapes['y_off'])
        pygame.draw.rect(self.screen, next_shapes_container['color'],
                         (x, y, width, height),
                         width=2)
        self.rectangles.append({"rect":pygame.Rect(x, y, width, height),
                               "name":'NEXT_SHAPE_CONTAINER'})
        text_surface = font.render('NEXT', True, color)
        self.screen.blit(text_surface, (x_t, y_t))

    def game_over_state_change(self):
        game_over = self.event_state.get_game_over()
        if game_over:
            self.event_state.set_event_state(3)

    def pause_text_blit(self, font, color):
        x, y, width, height = self.event_state.get_game_grid_coords()
        px, py = place_items_at_offset_percent(x, y, width, height, 0.25, 0.4)
        text_surface = font.render('PAUSED', True, color)
        self.screen.blit(text_surface, (px, py))


    def game_object_blit(self, grid_rows, font, color):
        if self.event_state.get_pause():
            self.pause_text_blit(font, color)
            return
        self.game_over_state_change()
        curr_shape = self.event_state.get_current_shape()
        b7 = self.event_state.get_bag_of_7()
        if curr_shape is None:
            b7 = self.load_shape_objects()
            b7.load_seven(grid_rows[0])
            b7.append_queue()
            shape = b7.get_queue_element()
            self.event_state.set_current_shape(shape)
        
        if len(b7.seven) == 0:
            b7.load_seven(grid_rows[0])
        
        if curr_shape == -1:
            shape = b7.get_queue_element()
            self.event_state.set_current_shape(shape)

        self.event_state.get_current_shape().draw_shape()

    def next_shapes_blit(self):
        b7 = self.event_state.get_bag_of_7()
        queue_3 = b7.queue[0:3]
        y_off = 0.1
        for q in queue_3:
            q.display_shape_in_next(y_off)
            y_off += 0.3
    
    def existing_shapes_blit(self):
        existing_shapes = self.event_state.get_existing_shapes()
        for shape in existing_shapes:
            shape.draw_shape()
    
    def movements(self, grid_rows):
        current_shape = self.event_state.get_current_shape()
        if current_shape == -1:
            return
        current_shape.move_shape_down(grid_rows)
        current_shape.move_shape_horizontal(grid_rows)

    def draw_existing_shapes(self, grid):
        block_size = self.constants['BLOCK_SIZE']
        BLACK = self.constants['GAME_CONTAINER_COLOR']
        for row in grid:
            for col in row:
                val = col['val']
                if val == -1:
                    continue
                x, y = col['coords']['x'], col['coords']['y']
                color = col['color']
                pygame.draw.rect(self.screen,
                                 color,
                                 (x, y, block_size, block_size),
                                 )
                pygame.draw.rect(self.screen,
                                 BLACK,
                                 (x, y, block_size, block_size),
                                 1
                                 )
                
    def preloader(self):
        existing_rects = self.event_state.get_menu_rectangles().get(4)
        if not self.rectangle_menu_set or existing_rects is None:
            self.event_state.set_menu_rectangles(self.rectangles,
                                        self.event_state.get_event_state())
            gmatrix = GridMatrix(self.constants, self.event_state)
            gmatrix.load_grid()
            self.rectangle_menu_set = True
            self.rectangles = []

    def level_change_check(self):
        lines = self.event_state.get_line_complete()
        curr_level = self.event_state.get_level()
        if lines%10 == 0 and lines > 0:
            if curr_level < 4:
                curr_level += 1
                self.event_state.set_level(curr_level)
                movement_delay = self.constants['movement_delay'][curr_level]
                self.event_state.set_movement_delay(movement_delay)

    def draw_screen(self):
        font = self.event_state.get_all_fonts()['text_font']
        color = self.game['font_color']
        grid_boundary_color = self.game['grid_boundary_color']
        block_size = self.game['block_size']
        self.scores_blit(font, color)
        self.grid_blit(grid_boundary_color, block_size)
        self.shape_blit(color, block_size, font)
        self.grid_exit_blit(color, font)
        self.preloader()
        grid_rows = self.event_state.get_grid_matrix()
        self.game_object_blit(grid_rows, font, color)
        if self.event_state.get_game_over():
            return
        self.draw_existing_shapes(grid_rows)
        self.movements(grid_rows)
        self.next_shapes_blit()
        self.event_state.set_game_over(detect_game_over(grid_rows))
        lc = detect_line_complete(grid_rows, self.event_state, self.constants)
        self.event_state.set_line_complete(lc)
        self.event_state.set_game_over(detect_game_over(grid_rows))
        self.level_change_check()
        

class MainMenu(Screen):
    def __init__(self, constants, title, menu, event_state, screen):
        self.constants = constants
        self.title = title
        self.menu = menu
        self.event_state = event_state
        self.screen = screen
    
    def draw_screen(self):
        elements = self.menu['elements']
        font = self.event_state.get_all_fonts()['other_fonts']
        rectangles = []
        for idx, v in enumerate(elements):
            x, y, width, height = self.draw_menu_boxes(self.menu,
                                                    self.event_state, v)
            color = self.menu['font_color']
            pygame.draw.rect(self.screen, color,
                            (x, y, width, height),
                            width=self.menu['box_line_width'])
            text_surface = font.render(v, True, color)
            name_coords = center_elements(x, y, width, height,
                                        text_surface.get_width(),
                                        text_surface.get_height())
            self.screen.blit(text_surface, name_coords)
            rectangles.append({"rect":pygame.Rect(x, y, width, height),
                               "name":v})
            self.event_state.set_menu_rectangles(rectangles,
                                                self.event_state.get_event_state())
            
        title_coords = self.menu['title_coords']
        self.title.draw_title("Tetris", title_coords)

def read_json(path):
    with open(path, 'r') as fp:
        payload = json.load(fp)
    return payload

def write_json(path, content):
    with open(path,'w') as fp:
        json.dump(content, fp)
def place_item_at_screen_center(screen_width, screen_height,
                                 entity_width,
                                   entity_height,
                                     padding=5,
                                     x_start=0,
                                     y_start=0):
    horiz_center = screen_width//2
    vert_center = screen_height//2
    x_origin = horiz_center - (entity_width//2)
    x_origin += x_start
    y_origin = vert_center - (entity_height//2)
    y_origin += y_start
    return x_origin, y_origin, entity_width, entity_height

def calculate_grid_dims(container_origin_x,
                        container_origin_y,
                        container_width,
                        container_height,
                        block_size,
                        grid_rows,
                        grid_cols,
                        ):
    width = grid_cols * block_size
    height = grid_rows * block_size
    place_dims = place_item_at_screen_center(container_width, 
                                             container_height,
                                             width,
                                             height,
                                             x_start=container_origin_x,
                                             y_start=container_origin_y)
    place_dims = [int(x) for x in place_dims]
    return place_dims

def get_boundary_dims(x, y, w, h, lw):
    boundary = {"width": lw,
                'boundary':[x, y, w, h]}
    return boundary
    
def calculate_boundaries_container(grid_x,
                                  grid_y,
                                  grid_width,
                                  grid_height):
    left_boundary = 0
    right_boundary = grid_x + grid_width
    start_y = grid_y
    block_size = grid_x
    boundaries = []
    while start_y <= grid_height:
        boundary_l1 = get_boundary_dims(left_boundary,
                                        start_y,
                                        block_size,
                                        block_size,
                                        1)
        boundary_l2 = get_boundary_dims(left_boundary+1, start_y+1,
                                        block_size-1, block_size-1, 0)
        boundary_r1 = get_boundary_dims(right_boundary, start_y,
                                        block_size, block_size, 1)
        boundary_r2 = get_boundary_dims(right_boundary+1, start_y+1,
                                        block_size-1, block_size-1, 0)
        boundaries.extend([boundary_l1, boundary_l2,
                          boundary_r1, boundary_r2])
        start_y += block_size
    return boundaries

def calculate_title_coords(grid_x,
                           grid_y,
                           grid_width,
                           grid_height,
                           x_off, y_off):
    x = grid_x + (grid_width*x_off)
    y = grid_y + (grid_height*y_off)
    return x, y

def center_elements(cont_x, cont_y,
                       cont_width, cont_height,
                       element_width, element_height):
    x_center = cont_x + cont_width//2
    x = x_center - element_width//2
    y_center = cont_y + cont_height//2
    y = y_center - element_height//2
    return x, y

def place_items_at_offset_percent(cont_x,
                                  cont_y,
                                  cont_width,
                                  cont_height,
                                  x_off,
                                  y_off):
    x = cont_x + (cont_width * x_off)
    y = cont_y + (cont_height * y_off)
    return x, y

def calculate_menu_boxes(menu, container_dims, width, height):
    x_cont, y_cont = container_dims['cont_x'], container_dims['cont_y']
    x_menu, y_menu = menu['x_off'], menu['y_off']
    w_container, h_container = container_dims['cont_width'],\
          container_dims['cont_height']
    x = x_cont + (w_container * x_menu)
    y = y_cont + (h_container * y_menu)
    width = w_container * width
    height = h_container * height
    return x, y, width, height

def calculate_shape_pos(grid_row, shape):
    if shape == 'I_SHAPE':
        rand_num = random.randint(0, len(grid_row)-1)
    elif (shape == 'S_SHAPE') or (shape == 'Z_SHAPE') or \
        shape == 'T_SHAPE':
        rand_num = random.randint(0, len(grid_row)-3)
    elif (shape == 'L_SHAPE') or (shape == 'J_SHAPE') or \
        (shape == 'O_SHAPE'):
        rand_num = random.randint(0, len(grid_row)-2)
    coords = grid_row[rand_num]['coords']
    return coords['x'], coords['y'], rand_num

def get_x_y_block_count(current_shape):
    all_rects = current_shape.all_rects
    x_count, y_count = [], []
    for rect in all_rects:
        x_count.append(rect.x)
        y_count.append(rect.y)
    x_count = len(set(x_count))
    y_count = len(set(y_count))
    return x_count, y_count
    
    



def adjust_speeds(event_state, constants):
    movement_delays = constants['movement_delay']
    level = event_state.get_level()
    delay = movement_delays[level]
    return delay

def lines_rearrangement(grid_cells, lines_idx):
    for idx in lines_idx:
        move_down_idx = idx-1
        for x in range(move_down_idx, 1, -1):
            for col in range(len(grid_cells[0])):
                curr_col = grid_cells[x][col].get('color')
                curr_val = grid_cells[x][col]['val']
                grid_cells[x+1][col]['val'] = curr_val
                grid_cells[x+1][col]['color'] = curr_col
        
def lines_rem(grid_cells, lines_idx):
    if len(lines_idx) == 0:
        return
    for idx in lines_idx:
        for col in range(len(grid_cells[0])):
            grid_cells[idx][col]['val'] = -1
            grid_cells[idx][col]['color'] = None
    
    lines_rearrangement(grid_cells, lines_idx)
    # for x in range(move_down_idx, 1, -1):
    #     grid_cells[x+1] = grid_cells[x]

def detect_line_complete(grid_cells, event_state, constants):
    line_completes = 0
    line_rows_idx = []
    for idx, row in enumerate(grid_cells):
        complete = True
        for col in row:
            if col['val'] == -1:
                complete = False
                break
        if complete:
            line_completes += 1
            line_rows_idx.append(idx)
    lines_rem(grid_cells, line_rows_idx)
    score_calculator(event_state, constants, 'lines', line_completes)
    return line_completes

def detect_game_over(grid_cells):
    start = 0
    for idx, row in enumerate(grid_cells):
        for col in row:
            if col['val'] == 1:
                return True
        start += 1
        if start >= 2:
            break
    return False

def score_calculator(event_state, constants,
                    scoring_type='placed',
                    lines_cleared=None):
    level = event_state.get_level()
    score_val = constants['scores_awarded'][level]
    curr_score = event_state.get_score()
    if scoring_type == 'placed':
        movement_delay = constants['movement_delay'][level]
        placed = 'placed'
        if event_state.get_movement_delay() < movement_delay:
            placed = 'placed_fast'
        event_state.set_score(curr_score + score_val[placed])
    else:
        lc_score = score_val['lines'].get(lines_cleared, 0)
        event_state.set_score(curr_score + int(lc_score))




class GuiCollisions:
    def __init__(self, constants, event_state):
        self.constants = constants
        self.event_state = event_state
        self.func_mapper = {0:self.main_menu_collisions,
                            4:self.game_screen_collisions,
                            3:self.game_over_collisions}

    def main_menu_collisions(self, name):
        if name.lower() == "start":
            self.event_state.set_current_shape(None)
            self.event_state.set_bag_of_7(None)
            self.event_state.set_event_state(4)
            self.event_state.set_score(0)
            self.event_state.set_verticle_speed(self.constants['BLOCK_SIZE'])
            
        if name.lower() == "highscores":
            print("Not Implemented Yet")
            pass
        if name.lower() == "about":
            print("Not Implemented Yet")
            pass
        if name.lower() == "exit":
            self.event_state.set_running(False)
    
    def level_score_reset(self):
        self.event_state.set_game_over(False)
        self.event_state.set_score(0)
        self.event_state.set_current_shape(None)
        self.event_state.set_level(1)
        movement_delay = self.constants['movement_delay'][1]
        self.event_state.set_movement_delay(movement_delay)
        
    def game_screen_collisions(self, name):
        if name.lower() == "exit":
            self.level_score_reset()
            self.event_state.set_event_state(0)
    
    def game_over_collisions(self, name):
        self.level_score_reset()
        if name.lower() == 'play_again':
            self.event_state.set_event_state(4)
        elif name.lower() == 'exit':
            self.event_state.set_event_state(0)

    def mouse_down_collisions(self):
        state = self.event_state.get_event_state()
        rectangles = self.event_state.get_menu_rectangles()
        rectangles = rectangles[state]
        mouse_x, mouse_y = self.event_state.get_mouse_pos()
        for rect_data in rectangles:
            if rect_data["rect"].collidepoint(mouse_x, mouse_y):
                func_handle = self.func_mapper[state]
                func_handle(rect_data['name'])
            
            
class StateLoader:
    def __init__(self, constants, event_state, screen):
        self.constants = constants
        self.event_state = event_state
        self.screen = screen
    
    def load_fonts(self):
        fonts = {'title':{}}
        states = self.event_state.get_all_event_states()
        for k, v in states.items():
            font_size = self.constants['TITLE_SIZES'][v]
            font_path = self.constants['TITLE_FONT']
            fnt = pygame.font.Font(font_path, font_size)
            fonts['title'][k] = fnt
        other_fonts = self.constants['menu_title_font']
        size, path = other_fonts['size'], other_fonts['path']
        other_fnt = pygame.font.Font(path, size)
        fonts['other_fonts'] = other_fnt

        text_font = other_fonts = self.constants['text_font']
        size, path = text_font['size'], text_font['path']
        text_fnt = pygame.font.Font(path, size)
        fonts['text_font'] = text_fnt

        self.fonts = fonts
        self.event_state.set_fonts(fonts)

    def load_speeds(self):
        bsize = self.constants['BLOCK_SIZE']
        self.event_state.set_verticle_speed(bsize)
        # self.event_state.set_horizontal_speed(bsize)

class GameScreen:
    def __init__(self, screen, constants, event_state):
        self.screen = screen
        display_info = pygame.display.Info()
        self.screen_width = display_info.current_w
        self.screen_height = display_info.current_h
        self.constants = constants
        self.inititialized = False
        self.event_state = event_state

    def draw_game_container(self, color):
        cont_width, cont_height = self.screen_width-50, self.screen_height
        dimensions = place_item_at_screen_center(self.screen_width,
                                           self.screen_height,
                                           cont_width, cont_height)
        self.grid_start_x = dimensions[0]
        self.grid_start_y = dimensions[1]
        self.container_width = dimensions[2]
        self.container_height = dimensions[3]
        self.event_state.set_container_coords(self.grid_start_x, 
                                              self.grid_start_y,
                                              self.container_width,
                                              self.container_height)

        pygame.draw.rect(self.screen, color, dimensions)

    def draw_boundaries(self):
        random_colors = self.constants['RANDOM_COLORS']
        boundaries \
            = calculate_boundaries_container(self.grid_start_x,
                                             self.grid_start_y,
                                             self.container_width,
                                             self.container_height)
        cidx = 0
        for x in boundaries:
            boundary = x['boundary']
            line_width = x['width']
            color_random = random_colors[cidx]
            cidx += 1
            pygame.draw.rect(self.screen, color_random, boundary, width=line_width)
            if cidx >= len(random_colors):
                cidx = 0
        
        


    # def draw_grid_container(self, color):
    #     block_size = self.constants['BLOCK_SIZE']
    #     grid_rows, grid_cols = self.constants['GRID_BLOCKS']
    #     dimensions = calculate_grid_dims(self.grid_start_x,
    #                                      self.grid_start_y,
    #                                      self.container_width,
    #                                      self.container_height,
    #                                      block_size,
    #                                      grid_rows,
    #                                      grid_cols)
    #     pygame.draw.rect(self.screen, color, dimensions)


class LoadScreenState:
    def __init__(self, constants, title, event_state, screen):
        self.constants = constants
        self.title = title
        self.event_state = event_state
        self.screen = screen

    def create_state_objects(self):
        all_states = self.event_state.get_all_event_states()
        event_objects = {}
        for k, v in all_states.items():
            try:
                screen_path = self.constants[v]
                entity_dict = read_json(screen_path)
                if v == "main_menu":
                    state_obj = MainMenu(self.constants, self.title, entity_dict,
                                        self.event_state, self.screen)
                elif v == "game":
                    state_obj = GameScreenScreen(self.constants, self.title, entity_dict,
                                        self.event_state, self.screen)
                elif v == "game_over":
                    state_obj = GameOver(self.event_state, self.constants,
                                         self.screen, entity_dict)
                event_objects[v] = state_obj
            except Exception as e:
                print(str(e))
        self.event_objects = event_objects
        self.event_state.set_event_objects(event_objects)

    def draw_state(self):
        state = self.event_state.get_event_state()
        state_name = self.event_state.get_all_event_states()[state]
        state_obj = self.event_objects[state_name]
        state_obj.draw_screen()

class Title:
    def __init__(self, font, colors, screen, event_state):
        self.font = font
        self.colors = colors
        self.screen = screen
        self.event_state = event_state

    def draw_title(self, text, coords):
        text_surface = self.font.render(text, True, self.colors)
        container_coords = self.event_state.get_container_coords()
        coords = calculate_title_coords(
                                        container_coords['cont_x'],
                                        container_coords['cont_y'],
                                        container_coords['cont_width'],
                                        container_coords['cont_height'],
                                        coords['x_off'], coords['y_off'])
        self.screen.blit(text_surface, coords)

class EventHandle:
    def __init__(self, event_variables, gui_collisions, constants):
        self.events_mapper = {
            pygame.QUIT: self.quit_handler,
            pygame.KEYDOWN: self.keydown_handler,
            pygame.KEYUP: self.keyup_handler,
            pygame.MOUSEBUTTONDOWN: self.mousedown_handler,
            pygame.MOUSEBUTTONUP: self.mouseup_handler
        }
        self.event_variables = event_variables
        self.gui_collisions = gui_collisions
        self.constants = constants
        self.keys_pressed = {}

    def quit_handler(self, event):
        self.event_variables.set_running(False)
        sys.exit()

    def adjust_movement_speeds(self):
        pass

    def keydown_handler(self, event):
        if (event.key == pygame.K_q):
            self.event_variables.set_running(False)

        elif (event.key == pygame.K_DOWN):
            delay = adjust_speeds(self.event_variables, self.constants)
            self.event_variables.set_movement_delay(delay//6)

        elif(event.key == pygame.K_UP):
            curr_shape = self.event_variables.get_current_shape()
            curr_shape.increment_current_rotation()
        
        elif(event.key == pygame.K_SPACE):
            curr_pause = self.event_variables.get_pause()
            self.event_variables.set_pause(not curr_pause)
        
    def keyup_handler(self, event):
        if (event.key == pygame.K_DOWN):
            delay = adjust_speeds(self.event_variables, self.constants)
            self.event_variables.set_movement_delay(delay)

        if event.key in [pygame.K_LEFT, pygame.K_RIGHT]:
            self.keys_pressed.pop(event.key, None)

    def mousedown_handler(self, event):
        self.event_variables.set_is_mouse_pressed(True)
        self.gui_collisions.mouse_down_collisions()
        

    def mouseup_handler(self, event):
        self.event_variables.set_is_mouse_pressed(False)


    def handle_event(self, event):
        type_func = self.events_mapper.get(event.type)
        if type_func:
            type_func(event)

        keys = pygame.key.get_pressed()
        self.event_variables.set_left_pressed(keys[pygame.K_LEFT])
        self.event_variables.set_right_pressed(keys[pygame.K_RIGHT])

class EventVariables:
    def __init__(self):
        self._running = True
        self._container_coords = {}
        self._event_state = 0
        self._states = {0:"main_menu",
                       1:"highscore",
                       2:"pause_menu",
                       3:"game_over",
                       4:"game"}
        self._fonts = None
        self.event_objects = None
        self._menu_rectangles = None
        self._mouse_pos = None
        self._is_mouse_pressed = False
        self._score = 0
        self._bag_of_7 = None
        self._current_shape = None
        self._verticle_speed = 0
        self._horizontal_speed = 0
        self._fps = 60
        self._movement_delay = 400
        self._elapsed_seconds = 0
        self._prev_movement = 0
        self._level = 1
        self._left_pressed = False
        self._right_pressed = False
        self._horiz_delay = 60
        self._prev_horiz_mov = 0
        self._game_grid_coords = None
        self._boundary_states = None
        self._left_move = True
        self._right_move = True
        self._bottom_move = True
        self._grid_matrix = []
        self._existing_shapes = []
        self._game_over = False
        self._pause = False
        self._line_completes = 0

    def set_line_complete(self, lc):
        self._line_completes += lc
    
    def get_line_complete(self):
        return self._line_completes
    
    def set_pause(self, p):
        self._pause = p
    
    def get_pause(self):
        return self._pause

    def get_game_over(self):
        return self._game_over
    
    def set_game_over(self, gameover):
        self._game_over = gameover

    def set_existing_shapes(self, shape):
        self._existing_shapes.append(shape)

    def get_existing_shapes(self):
        return self._existing_shapes

    def set_grid_matrix(self, matrix):
        self._grid_matrix = matrix

    def get_grid_matrix(self):
        return self._grid_matrix

    def set_left_move(self, value):
        self._left_move = value

    def get_left_move(self):
        return self._left_move

    def set_right_move(self, value):
        self._right_move = value

    def get_right_move(self):
        return self._right_move

    def set_bottom_move(self, value):
        self._bottom_move = value

    def get_bottom_move(self):
        return self._bottom_move

    def set_boundary_rect(self, boundary):
        self._boundary_states = boundary

    def get_boundary_rect(self):
        return self._boundary_states

    def set_game_grid_coords(self, coords):
        self._game_grid_coords = coords

    def get_game_grid_coords(self):
        return self._game_grid_coords
    
    def get_prev_horiz_movement(self):
        return self._prev_horiz_mov
    
    def set_prev_horiz_movement(self, secs):
        self._prev_horiz_mov = secs

    def get_horiz_delay(self):
        return self._horiz_delay

    def set_left_pressed(self, l):
        self._left_pressed = l

    def get_left_pressed(self):
        return self._left_pressed
    
    def set_right_pressed(self, r):
        self._right_pressed = r

    def get_right_pressed(self):
        return self._right_pressed
    
    def set_level(self, level):
        self._level = level

    def get_level(self):
        return self._level

    def set_prev_movement(self, prev):
        self._prev_movement = prev
    
    def get_prev_movement(self):
        return self._prev_movement

    def set_elapsed_seconds(self, secs):
        self._elapsed_seconds = secs

    def get_elapsed_seconds(self):
        return self._elapsed_seconds

    def set_movement_delay(self, delay):
        self._movement_delay = delay

    def get_movement_delay(self):
        return self._movement_delay
    
    def get_fps(self):
        return self._fps

    def set_verticle_speed(self, speed):
        self._verticle_speed = speed

    def get_verticle_speed(self):
        return self._verticle_speed
    
    def set_horizontal_speed(self, speed):
        self._horizontal_speed = speed

    def get_horizontal_speed(self):
        return self._horizontal_speed
    
    def set_current_shape(self, shape):
        self._current_shape = shape

    def get_current_shape(self):
        return self._current_shape

    def set_score(self, score):
        self._score = score

    def get_score(self):
        return self._score
    
    def set_is_mouse_pressed(self, val: bool):
        self._is_mouse_pressed = val
    
    def get_is_mouse_pressed(self):
        return self._is_mouse_pressed

    def set_running(self, value: bool):
        self._running=value

    def get_running(self):
        return self._running
    
    def set_fonts(self, fonts):
        self._fonts = fonts

    def get_font(self, font_key, state):
        return self._fonts[font_key][state]

    def get_all_fonts(self):
        return self._fonts
    
    def set_container_coords(self, x, y, width, height):
        self._container_coords['cont_x'] = x
        self._container_coords['cont_y'] = y
        self._container_coords['cont_width'] = width
        self._container_coords['cont_height'] = height

    def get_container_coords(self):
        return self._container_coords
    
    def set_event_state(self, event_state):
        self._event_state = event_state

    def get_event_state(self):
        return self._event_state
    
    def get_all_event_states(self):
        return self._states
    
    def set_event_objects(self, event_objects):
        self.event_objects = event_objects
    
    def get_event_objects(self):
        return self.event_objects
    
    def set_menu_rectangles(self, rectangles, state):
        self._menu_rectangles = {state: rectangles}

    def get_menu_rectangles(self):
        return self._menu_rectangles
    
    def set_mouse_pos(self, mouse_pos):
        self._mouse_pos = mouse_pos

    def get_mouse_pos(self):
        return self._mouse_pos
    
    def set_bag_of_7(self, bag_of_seven):
        self._bag_of_7 = bag_of_seven

    def get_bag_of_7(self):
        return self._bag_of_7
constants = {}
constants['SCREEN_WIDTH'] = 1920
constants['SCREEN_HEIGHT'] = 1080
constants['FULL_SCREEN'] = True
constants['BACKGROUND_COLOR'] = (245, 240, 240)
constants['GAME_CONTAINER_COLOR'] = (0, 0, 0)
constants['GRAY'] = (191, 191, 191)
constants['BLOCK_SIZE'] = 35
constants['GRID_BLOCKS'] = (20, 10)
constants['GRID_ORIGIN'] = (50, 70)
constants['TITLE_SIZES'] = {"main_menu": 48, 'pause_menu': 24,
                            'highscore': 30, 'game_over': 36,
                            'game': 12}
constants['TITLE_COLOR'] = (132, 237, 245)
constants['TITLE_FONT'] = "assets/fonts/title_font.otf"
constants['RANDOM_COLORS'] = [(92, 206, 255),
                              (31, 47, 224),
                              (224, 109, 247),
                              (212, 38, 87)]
constants['main_menu'] = "assets/screens/main_menu.json"
constants['game'] = "assets/screens/game_screen.json"
constants['game_over'] = "assets/screens/game_over.json"
constants['menu_title_font'] = {"size": 32, "color": (
    255, 255, 255), 'path': "assets/fonts/menu_items.ttf"}
constants['text_font'] = {"size": 32, "color": (
    255, 255, 255), 'path': "assets/fonts/text_font.ttf"}
constants['shapes'] = "assets/screens/shapes_rotations.json"
constants['movement_delay'] = {1: 400,
                               2: 250,
                               3: 150,
                               4: 100}
constants['level_change_lines'] = 10 

constants['scores_awarded'] = {1: {"lines": {1: "60",
                                             2: "120",
                                             3: "360",
                                             4: "1000"},
                                   'placed': 20,
                                   'placed_fast': 30},
                               2: {"lines": {1: "80",
                                             2: "160",
                                             3: "480",
                                             4: "1200"},
                                   'placed': 25,
                                   'placed_fast': 35},
                               3: {"lines": {1: "100",
                                             2: "200",
                                             3: "600",
                                             4: "1500"},
                                   'placed': 30,
                                   'placed_fast': 40},
                               4: {"lines": {1: "120",
                                             2: "240",
                                             3: "720",
                                             4: "1800"},
                                   'placed': 40,
                                   'placed_fast': 50}}

# constants['main_menu'] = "assets/screens/main_menu.json"
# constants['main_menu'] = "assets/screens/main_menu.json"


class GameRunner:

    def __init__(self):

        self.SCREEN_HEIGHT = constants['SCREEN_HEIGHT']

        self.SCREEN_WIDTH = constants['SCREEN_WIDTH']

        self.full_screen = constants['FULL_SCREEN']

        self.background_color = constants['BACKGROUND_COLOR']

        self.game_container_color = constants['GAME_CONTAINER_COLOR']

        self.event_variable = EventVariables()

        self.gui_collisions = GuiCollisions(constants, self.event_variable)

        self.event_handle = EventHandle(self.event_variable,
        
                                                    self.gui_collisions, constants)
                                                    


    def pygame_initializer(self):
        
        pygame.init()
        
        self.screen = pygame.display.set_mode((self.SCREEN_WIDTH, self.SCREEN_HEIGHT), pygame.FULLSCREEN)
        
        self.game_screen = GameScreen(self.screen, constants, self.event_variable,
        
                                      )
                                      
        self.states = StateLoader(constants, self.event_variable, self.screen)
        
        self.states.load_fonts()
        
        self.states.load_speeds()
        
        title_font = self.event_variable.get_font("title",
        
                                                  self.event_variable.get_event_state())
                                                  
        self.title = Title(font=title_font,
        
                                    colors=constants['TITLE_COLOR'],
                                    
                                    screen=self.screen,
                                    
                                    event_state=self.event_variable)
                                    
        self.screen_objects = LoadScreenState(constants, 
        
                                              self.title,
                                              
                                              self.event_variable, self.screen)
                                              
        self.screen_objects.create_state_objects()

        



    def events(self):

        for event in pygame.event.get():

            self.event_handle.handle_event(event)



    def game_run(self):

        self.pygame_initializer()

        clock = pygame.time.Clock()  # Create a Clock object

        FPS = self.event_variable.get_fps()

        start_time = pygame.time.get_ticks()  # Get start time in milliseconds

        while self.event_variable.get_running():

            self.events()

            self.screen.fill(self.background_color)
            
            self.game_screen.draw_game_container(self.game_container_color)
            
            self.game_screen.draw_boundaries()
            
            self.screen_objects.draw_state()
            
            self.event_variable.set_mouse_pos(pygame.mouse.get_pos())
            
            current_time = pygame.time.get_ticks()
            
            elapsed_time = current_time - start_time
            # elapsed_seconds = elapsed_time // 1000
            
            self.event_variable.set_elapsed_seconds(elapsed_time)
            
            pygame.display.flip()
            
            clock.tick(FPS)
            
        sys.exit()
        




gr = GameRunner()

gr.game_run()