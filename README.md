# StealthPath

Detection-aware attack path planning in Active Directory.

## Research Direction

StealthPath investigates how different attack-path planners behave
when evaluated on Active Directory graphs while considering detection
exposure.

## Planners

1. Shortest-path planner
2. Risk-weighted planner
3. Reinforcement-learning planner

## Current Stage

Initial graph representation and shortest-path baseline validation.

The project is being developed incrementally, starting with toy graphs
before moving to synthetic and real Active Directory data.

## Dataset

The initial experiments use small toy graphs for validation.

Synthetic Active Directory graphs and an authorized real SharpHound
collection will be considered only after the basic planning pipeline
has been verified.

## Research Status

This project does not assume that reinforcement learning or
detection-aware planning will outperform simpler approaches.
Performance will be determined experimentally.