import math
from typing import List, Tuple

def calculate_distance(p1: Tuple[float, float], p2: Tuple[float, float]) -> float:
    return math.hypot(p1[0] - p2[0], p1[1] - p2[1])

def solve_tsp(points: List[Tuple[float, float]], start_index: int = 0) -> List[int]:
    """
    Nearest Neighbor Heuristic for TSP.
    points: List of (lat, lon) tuples
    Returns: List of indices representing the path
    """
    if not points:
        return []
        
    n = len(points)
    visited = [False] * n
    path = [start_index]
    visited[start_index] = True
    
    current_index = start_index
    
    for _ in range(n - 1):
        nearest_dist = float('inf')
        nearest_index = -1
        
        for i in range(n):
            if not visited[i]:
                dist = calculate_distance(points[current_index], points[i])
                if dist < nearest_dist:
                    nearest_dist = dist
                    nearest_index = i
        
        if nearest_index != -1:
            visited[nearest_index] = True
            path.append(nearest_index)
            current_index = nearest_index
            
    return path
