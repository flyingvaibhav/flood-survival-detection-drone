import heapq
import numpy as np
from typing import List, Tuple, Optional

class Node:
    def __init__(self, position: Tuple[int, int], parent=None):
        self.position = position
        self.parent = parent
        self.g = 0  # Cost from start to current node
        self.h = 0  # Heuristic (estimated cost from current to end)
        self.f = 0  # Total cost

    def __eq__(self, other):
        return self.position == other.position
    
    def __lt__(self, other):
        return self.f < other.f

def heuristic(a: Tuple[int, int], b: Tuple[int, int]) -> float:
    # Euclidean distance
    return ((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2) ** 0.5

def astar_search(grid: np.ndarray, start: Tuple[int, int], end: Tuple[int, int]) -> Optional[List[Tuple[int, int]]]:
    """
    A* Pathfinding Algorithm.
    grid: 2D numpy array where 0 is walkable and 1 is obstacle.
    start: (x, y) tuple
    end: (x, y) tuple
    Returns: List of (x, y) tuples representing the path.
    """
    
    # Check bounds
    h, w = grid.shape
    if not (0 <= start[0] < w and 0 <= start[1] < h):
        return None
    if not (0 <= end[0] < w and 0 <= end[1] < h):
        return None
        
    # If start or end is an obstacle, return None
    # Note: In our simulation, we might assume open air, but this is good for robustness
    if grid[end[1], end[0]] == 1:
        return None

    start_node = Node(start, None)
    end_node = Node(end, None)

    open_list = []
    closed_set = set()

    heapq.heappush(open_list, start_node)

    while open_list:
        current_node = heapq.heappop(open_list)
        closed_set.add(current_node.position)

        # Found the goal
        if current_node == end_node:
            path = []
            current = current_node
            while current is not None:
                path.append(current.position)
                current = current.parent
            return path[::-1]  # Return reversed path

        # Generate children (8 directions)
        children = []
        for new_position in [(0, -1), (0, 1), (-1, 0), (1, 0), (-1, -1), (-1, 1), (1, -1), (1, 1)]:
            node_position = (current_node.position[0] + new_position[0], current_node.position[1] + new_position[1])

            # Check within range
            if node_position[0] > (w - 1) or node_position[0] < 0 or node_position[1] > (h - 1) or node_position[1] < 0:
                continue

            # Check walkable terrain
            if grid[node_position[1], node_position[0]] != 0:
                continue

            new_node = Node(node_position, current_node)
            children.append(new_node)

        for child in children:
            if child.position in closed_set:
                continue

            child.g = current_node.g + 1
            child.h = heuristic(child.position, end_node.position)
            child.f = child.g + child.h

            # Check if child is already in the open list with a lower g cost
            # This is a simplified check; strictly we should update if we find a better path
            # But for grid based, this is usually sufficient or we can just push duplicates
            heapq.heappush(open_list, child)

    return None
