- [ ] Lit Review
	- [ ] Universal design focus
		- [ ] Inamura sensei notes:
		- [ ] Inclusive Design
		- [ ] Computation Design
		- [ ] Meta Design
	- [ ] Other fan attempts
		- [ ] Ship of Harkinian 
- [ ] Proposal
	- [ ] Implementing RS
		- [ ] Be more concrete about process/guidelines
			- [ ] Might go after Implementation section
- [ ] Implementation
	- [ ] Overview
	- [ ] Structure
	- [ ] Samples
		- [ ] Designing a good audio display
	- [ ] Issues
- [ ] Graphics!
	- [ ] Intro
	- [ ] Lit review
	- [ ] Structure
	- [ ] Implementation

## Main issues
- Doesn't address universal/computational/meta design in lit review
- Doesn't do enough audification review 
- Doesn't show enough "similarish" work
- Doesn't clarify the process of general implementation 
	- Use other games to demonstrate
- Doesn't have implementation section!
## Principal Additions
## Implementation
- Software used 
- Structural overview
- Samples of decisions and audio
- Issues 
- Limitations 
- MAKE GRAPHICS
 
- Discuss required attributes 
	- lost frames
- Discuss difficulties of losing objects
	- Collides with score card 
	- Hit can make either object disappear 
- Discuss difficulties of hit detection
	- Distance isn't always a valid measure 
		- Close misses on top or bottom
	- Pong has irregular collision detection behavior 
		- Balls that should miss might get caught 
	- Assumes hit is captured in frame
		- Frame drops or other visual issues might obscure a hit 
- Discuss Fan projects
	- Ship of Harkinian etc
- Discuss dependency issues 
	- Ball requires P1 information for calculation 
		- Who should manage an audio object?
## Implementation Difficulties 
- Functionality of QT 
	- No pitch manipulate for Spatial Audio 
- Merging disparate software libraries 
### Designing a good Audio Display
- Many iterations and variations 
	- All of them tend to lose some key data
- Generic HRTFs 
	- Demand generic solutions that lose out on some opportunities
		- Elevation understanding
		- Cone of Confusion 
- Fast-paced nature of games
	- Demands some clever design
		- Need to understand the *trajectory* of actions, not just their current state 

## Presentation notes
- Needs updates
- Limited game scope
	- Discuss and acknowledge 
- Further explain implementation process
	- guidelines for future researchers
	- Clearly and visually explain how RS is added to a gain
- Cover general computing accessibility and universal/inclusive design in Lit Review
- Considerations
	- How would you involve actual users (visually impaired ones) in the process 
-