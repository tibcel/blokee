from turtle import clear
import pandas as pd
import numpy as np


def get_rotations_of_piece(piece, number_of_rotations, mirror=True):
    pieces_dictionary = {}
    pieces_dictionary["l0"]=piece

    for i in range(1, number_of_rotations):
        print(f"Processing rotation number {i}")
        piece = rotate_piece(piece)       
        #piece.to_csv(f"piesa_rotatia_{i}.csv", header=False, index=False)
        pieces_dictionary[f"l{i}"] = piece

    if mirror:
        piece = mirror_piece(pieces_dictionary["l0"])
        pieces_dictionary[f"m_l0"] = piece

        for i in range(1, number_of_rotations):
            print(f"Processing rotation number {i}")
            piece = rotate_piece(piece)       
            #piece.to_csv(f"piesa_rotatia_mirror_{i}.csv", header=False, index=False)
            pieces_dictionary[f"m_l{number_of_rotations - i}"] = piece

    return pieces_dictionary

def rotate_piece(piece):
    intermediary_piece = piece.values.tolist()
    piece = pd.DataFrame([[intermediary_piece[j][i] for j in range(len(intermediary_piece))] for i in range(len(intermediary_piece[0])-1,-1,-1)])
    return piece

def mirror_piece(piece):
    return piece.iloc[:, ::-1]


def get_area_around_corner(whole_table, corner_coordinates, length):

    table_length = len(whole_table)
    x = corner_coordinates[0]
    y = corner_coordinates[1]

    x_start_index = x - length
    y_start_index = y -length

    x_end_index = x + length
    y_end_index = y + length

    if x_start_index < 0:
        x_start_index = 0

    if y_start_index < 0:
        y_start_index = 0

    if y < length:
        y= length

    if x_end_index > table_length:
        x_end_index = table_length

    if y_end_index > table_length:
        y_end_index = table_length
    elif y_end_index < table_length:
        y_end_index = y_end_index+1
        
    return (whole_table.iloc[x_start_index:x_end_index, y_start_index:y_end_index],[x_start_index, y_start_index])

def get_valid_positions(table, piece, starting_position, score, piece_name, rotation):
    print(f"PIECEEEE")
    print(piece)
    piece_height = piece.shape[0]
    piece_width = piece.shape[1]
    print(f"p_h {piece_height} p_w {piece_width}")

    table_height = table.shape[0]
    table_width = table.shape[1]
    print(f"t_h {table_height} t_w {table_width}")

    piece_metrics = []
    #Parallel(n_jobs=2)(delayed(sqrt_func)(i, j) for i in range(5) for j in range(2))

    for i in range(0, table_height - piece_height + 1):
        for j in range(0, table_width - piece_width + 1):
            
            sliced_table = (table.iloc[i:i+piece_height, j:j+piece_width])
            resulted_table = (sliced_table.to_numpy() + piece.to_numpy())

            uniques = np.unique(resulted_table)
            if not (11 in uniques or 21 in uniques) and 31 in uniques :
                print(f"valid position at {i} {j}")
                #daca piesa e pusa peste un colt de al nostru 30 + 1 = 31
                player_corners_covered = np.count_nonzero(resulted_table == 31)

                #colturile inamicilor sunt 40 50 60 luate in mod arbitrar
                enemy_corners_covered = np.count_nonzero(resulted_table==41) + np.count_nonzero(resulted_table==51) + np.count_nonzero(resulted_table==61)

                #pozitia trebuie renormalizata deoarece prima oara e relativa mica (cea sliced)
                position = normalize_position([i,j], starting_position)

                #adaugam [x, y, player_corners_covered, enemy_corners_covered] in piece_metrics care este o lista de liste
                piece_metrics.append([piece_name, rotation, position[0], position[1], player_corners_covered, enemy_corners_covered, (int(score) + enemy_corners_covered*7 - player_corners_covered*3)])
                                
    return piece_metrics

def normalize_position(relative_position, starting_position):
    return [a + b for a, b in zip(relative_position, starting_position)]



def main(input_file, pieces_file, piece_name, corner_coordinates_uipath, no_of_rotations, is_mirror, score, save_to_path):
    """
    The main function which will be invoked from UiPath in a loop for each piece. Does not return anything, in the end it will
    write an excel file with columns columns=['piece', 'rotation', 'x', 'y', 'player_corners_covered', 'enemy_corners_covered']) for each PIECE
    
    input_file = path to the digitized version of the table after the corners have been set up
    pieces_file = path to the Excel which contains all of the pieces
    piece_name = the name of the sheet that corresponds to the piece
    corner_coordinate_uipath = string -> {x_y, x1_y1....}
    no_of_rotations = int
    is_mirror = bool
    score => the one from excel file
    save_to_path => where to save the file

    """

    whole_table = pd.read_excel(input_file, header=None)
    piece = pd.read_excel(pieces_file, header=None, sheet_name=piece_name)
    columns = ['piece', 'rotation', 'x', 'y', 'player_corners_covered', 'enemy_corners_covered', 'final_score']

    results_table = pd.DataFrame([], columns=columns)

    pieces_dictionary = {}

    #First we split by , to get all player corners
    for corner_coordinate_element in corner_coordinates_uipath.split(","):

        #split to get x and y
        corner_coordinates = tuple(int(n) for n in corner_coordinate_element.split("_"))

        #get area around corner, atm set up for 4 can become argument
        (sliced_table, starting_position) = get_area_around_corner(whole_table, corner_coordinates, max(piece.shape[0], piece.shape[1])+1)
        print("Starting Position: "+str(starting_position))

        #create a dictioary with all of the pieces rotation
        pieces_dictionary = get_rotations_of_piece(piece, int(no_of_rotations), bool(is_mirror))

        #for each possible rotation of piece get valid positions for current corner coordinates4

        for key in list(pieces_dictionary.keys()):
            #pieces_dictionary[key].to_csv(f"C:/Users/bibi/OneDrive/Documents/UiPath/cami/Workflows/Pytonu/csvs/{key}.csv", index=False)
            #print("PROCESSING "+key)
            valid_positions = get_valid_positions(sliced_table, pieces_dictionary[key], starting_position, score, piece_name, key)
            #print(str(valid_positions))
            results_table = results_table.append(pd.DataFrame(valid_positions, columns=columns), ignore_index=True)

        results_table.drop_duplicates(inplace=True)
        #results_table.to_excel(save_to_path, header=True, index=False, sheet_name=piece_name)
        results_table.to_csv(save_to_path, index=None)

#main("C:/Users/bibi/OneDrive/Documents/UiPath/cami/Workflows/Pytonu/corners.xlsx", "C:/Users/bibi/OneDrive/Documents/UiPath/cami/Workflows/Pytonu/Pieces.xlsx",
#"F", "7_10,9_10", 4, True, 40, "C:/Users/bibi/OneDrive/Documents/UiPath/cami/Workflows/Pytonu/results.xlsx")


# def validate_area_around_piece(table, piece, starting_position_x, starting_position_y):

#     for row in range(0, piece.shape[0]):
#         for column in range(0, piece.shape[1]):
#             if int(piece.iloc[row, column]) == 1:
#                 print(f"found 1 on {row}_{column} value" + str(piece[column][row]))
                
#                 x, y = starting_position_x+column, starting_position_y+row
#                 print(f"pozitia in tabela_mare a celulei {x}, {y} ")

#                 for i in [x-1,x+1]:
#                     print(f"lookign on cell {i}_{y} for 10 value in cell {str(table[i][y])}")
#                     if int(table[i][y]) == 10:
#                         return False

#                 for j in [y-1, y+1]:
#                     print(f"lookign on cell {x}_{j} for 10 value in cell{str(table[x][j])}")
#                     if int(table[x][j]) == 10:
#                         return False
    
#     return True


