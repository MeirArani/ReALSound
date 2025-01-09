# Overview 

## Basic Concepts

A **Game** can be modeled as a collection of two sets: States, and Entities.
Each state within a game (hereafter called game state) has: 
- State transition rules
- State logic
A state's 'logic' comprises all of the actions and behaviors of a given state. 
For example, a 'start' state in a racing game might play a musical jingle and display the text "Start!" on screen.
A state's transition rules, meanwhile, define the conditional requirements which transitions this state to another game state.
For example, the aforementioned "start" state may also have a 

Each entity, in a similar fashion, is also 



### Game 
- Overarching meta structure. 
- Attributes
	- Session data
		- time active
	- Active Entities 
	- Game States
- Behaviors
	- Receives Vision data from Vision Layer
		- Updates session data
		- Updates active entities
	- Notifies current state with Vision data 
### Game State
- Individual section of Game
- Attributes
	- State data
	- Transition Logic
	- Audio Logic
- Behaviors
	- Receives Vision data from Game
	- Updates state data
	- Sends Vision data to relevant Entities
	- Evaluates Audio logic
		- Plays Audio
	- Evaluates Transition Logic
		- Transitions 
### Entity
- Individual entity in game 
- Attributes
	- Entity data
		- Position
		- Traits
	- Entry States
- Behaviors
	- Receives vision data from game state
		- Updates entity data
	- Notifies current State
### Entity State
- Individual state of Entity
- Attributes 
	- Transition logic
	- Audio logic
- Behaviors
	- Evaluates Audio logic
		- Plays Audio
	- Evaluates Transition logic
		- Transitions 

## Layers

## VISION LAYER
- Translates game visuals into computational data
	- Defines a series of 'entities' that accurately describe the game state 
# State Machine
# State 