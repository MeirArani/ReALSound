# Intro (1 min)
- Universal, cross platform software
- AI/CV developments
- 3D audio developments
- Game industry / accessibility developments
	- Some software is being universalized, but accessibility tech is not
- **Statement:** There should be tools that universalize game accessibility development using modern advancement
	- We propose RS: which uses computer vision to analyze a game like a human does. 
		- Show diagram
# Lit Review (<1 min)
- Computer vision is now a very mature field
	- Many high quality ways to perform object detection / classification 
		- Traditional detection methods
		- ML/DL
			- YOLO
- Spatial Audio has advanced in recent years
	- Now many easy-to-use spatial audio libraries 
		- Common hardware support (airpods etc)
	- Makes use of human sound localization
		- HRTF etc
			- Mention HRTFs in weaknesses too
- Some game accessibility work in past
	- AGRIP
	- Very little involving AI or CV
	- SFVI
	- Other stuff mentioned in thesis
# Proposal
## Goal
- Convert a game's 'visual display' into a good 'audio display'
	- Give player all the important information using audio
- Or:
	1) Look at each frame of the game 
	2) Analyze image using CV algorithm 
	3) Convert analyzed data into spatial audio
## Structure:
- Vision Layer
	- **Input:** Picture of game
	- **Output:** Semantic information about game
- Decision Layer
	- **Input:** Semantic Information about game
	- **Output:** Spatial audio objects
- Audification Layer
	- **Input:** Spatial Audio objects
	- **Output:** Playback of spatial audio
## Method 
### Visual Analysis
- How does a computer 'understand' a game visually?
- First, we must define a game:
#### Defining a game:
Games are a collection of
	- Entities: Objects within a game that 'do' something
	- States: Contexts that entities live in
	- Rules: Laws specific to states that control entities and state transitions 
	- Attributes: Data about the game, states, or attributes
Use pong as an example 
- Games can be modeled as FSAs,
	- Very well studied theory
### Vision Layer
- Use computer vision/ML techniques to classify/detect game entities 
	- Paddles and ball in 'pong'
### 