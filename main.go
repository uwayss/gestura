package main

import (
	"bufio"
	"encoding/base64"
	"encoding/json"
	"flag"
	"fmt"
	"image"
	"image/color"
	"io"
	"log"
	"math"
	"os"
	"os/exec"
	"os/signal"
	"path/filepath"
	"strings"
	"syscall"
	"time"

	"github.com/gen2brain/beeep"
	"gocv.io/x/gocv"
)

// --- Constants ---
const (
	actionCooldown        = 1 * time.Second
	comboTimeout          = 1500 * time.Millisecond
	confirmationThreshold = 2 // Frames
)

// --- Data Structures for MediaPipe Output ---

type Landmark struct {
	X float64 `json:"x"`
	Y float64 `json:"y"`
	Z float64 `json:"z"`
}

type HandData struct {
	Handedness string     `json:"handedness"`
	Landmarks  []Landmark `json:"landmarks"`
}

type MediaPipeOutput struct {
	Hands []HandData `json:"hands"`
	Frame string     `json:"frame,omitempty"` // Base64 encoded frame for debug
	Error string     `json:"error,omitempty"`
}

// --- Data Structures for Gesture Recognition ---

type FingerStateMap map[string]string

type HandState struct {
	Handedness  string
	Orientation string
	Direction   string
	Fingers     FingerStateMap
}

type GestureConditions struct {
	Handedness  string         `json:"handedness,omitempty"`
	Orientation string         `json:"orientation,omitempty"`
	Direction   string         `json:"direction,omitempty"`
	Fingers     FingerStateMap `json:"fingers,omitempty"`
}

type GestureDefinition struct {
	Conditions GestureConditions `json:"conditions"`
}

// --- Main Application Struct ---

type App struct {
	debugMode         bool
	pythonCmd         *exec.Cmd
	pythonStdout      io.ReadCloser
	gestureDefs       map[string]GestureDefinition
	actionMap         map[string]string
	stabilizers       []*GestureStabilizer
	comboManager      *ComboManager
	lastActionTime    time.Time
	lastActionGesture string
	lastStableGesture string
	webcam            *gocv.Window
}

func NewApp(debug bool) (*App, error) {
	gestures, err := loadJSON[map[string]GestureDefinition]("gestures.json")
	if err != nil {
		return nil, fmt.Errorf("failed to load gestures: %w", err)
	}
	fmt.Printf("Loaded %d gesture definitions.\n", len(gestures))

	actions, err := loadJSON[map[string]string]("actions.json")
	if err != nil {
		return nil, fmt.Errorf("failed to load actions: %w", err)
	}
	fmt.Printf("Loaded %d action mappings.\n", len(actions))

	app := &App{
		debugMode:    debug,
		gestureDefs:  gestures,
		actionMap:    actions,
		comboManager: NewComboManager(),
		stabilizers: []*GestureStabilizer{
			NewGestureStabilizer(),
			NewGestureStabilizer(),
		},
	}

	if debug {
		app.webcam = gocv.NewWindow("Gestura - Go Debug")
	}

	return app, nil
}

func (a *App) Run() {
	a.startPythonHelper()
	defer a.Cleanup()

	c := make(chan os.Signal, 1)
	signal.Notify(c, os.Interrupt, syscall.SIGTERM)
	go func() {
		<-c
		fmt.Println("\nCaught interrupt signal.")
		a.Cleanup()
		os.Exit(0)
	}()

	if a.debugMode {
		fmt.Println("Running in DEBUG mode. Press 'q' in the window to quit.")
	} else {
		fmt.Println("Running in HEADLESS mode. Press Ctrl+C to quit.")
	}

	scanner := bufio.NewScanner(a.pythonStdout)
	buf := make([]byte, 0, 64*1024)
	scanner.Buffer(buf, 1024*1024)

	img := gocv.NewMat()
	defer img.Close()

	for scanner.Scan() {
		var output MediaPipeOutput
		if err := json.Unmarshal(scanner.Bytes(), &output); err != nil {
			log.Printf("Error unmarshalling JSON from Python: %v", err)
			continue
		}

		if output.Error != "" {
			log.Printf("Error from Python script: %s", output.Error)
			break
		}

		if a.debugMode {
			if output.Frame != "" {
				frameBytes, err := base64.StdEncoding.DecodeString(output.Frame)
				if err != nil {
					log.Printf("Error decoding base64 frame: %v", err)
					continue
				}
				img, err = gocv.IMDecode(frameBytes, gocv.IMReadColor)
				if err != nil {
					log.Printf("Error decoding image bytes: %v", err)
					continue
				}
			} else {
				img = gocv.NewMatWithSize(480, 640, gocv.MatTypeCV8UC3)
			}
		}

		var handsForRenderer []HandRenderData

		if len(output.Hands) > 0 {
			primaryHand := output.Hands[0]
			stabilizer := a.stabilizers[0]
			rawGesture, _ := a.recognizeGesture(primaryHand)
			stableGesture := stabilizer.Update(rawGesture)

			fmt.Printf("Hand 0 (%s) | Raw: %-15s -> Stable: %-15s\r", primaryHand.Handedness, Coalesce(rawGesture, "None"), Coalesce(stableGesture, "None"))

			if stableGesture != "" && stableGesture != a.lastStableGesture {
				a.lastStableGesture = stableGesture
				a.processActions(stableGesture)
			} else if stableGesture == "" {
				a.lastStableGesture = ""
			}

			if a.debugMode {
				for i, hand := range output.Hands {
					if i >= len(a.stabilizers) {
						break
					}
					hRaw, hState := a.recognizeGesture(hand)
					hStable := a.stabilizers[i].Update(hRaw)
					handsForRenderer = append(handsForRenderer, HandRenderData{
						HandData: hand, State: hState, RawGesture: hRaw, StableGesture: hStable,
					})
				}
			}
		} else {
			a.stabilizers[0].Update("")
			a.stabilizers[1].Update("")
			a.lastStableGesture = ""
			fmt.Printf("No hands detected...                                       \r")
		}

		if a.debugMode {
			if !img.Empty() {
				DrawDebugInfo(&img, handsForRenderer)
				a.webcam.IMShow(img)
				if a.webcam.WaitKey(1) == int('q') {
					break
				}
			}
		}
	}

	if err := scanner.Err(); err != nil {
		log.Printf("Error reading from python stdout: %v", err)
	}
}

func (a *App) startPythonHelper() {
	venvPython := "mediapipe_helper/venv/bin/python"
	scriptPath := "mediapipe_helper/mediapipe_helper.py"

	if _, err := os.Stat(venvPython); os.IsNotExist(err) {
		log.Fatalf("Python executable not found at %s. Did you run the setup commands?", venvPython)
	}

	args := []string{scriptPath}
	if a.debugMode {
		args = append(args, "--debug")
	}

	a.pythonCmd = exec.Command(venvPython, args...)
	stdout, err := a.pythonCmd.StdoutPipe()
	if err != nil {
		log.Fatalf("Error getting stdout pipe: %v", err)
	}
	a.pythonStdout = stdout
	a.pythonCmd.Stderr = os.Stderr

	if err := a.pythonCmd.Start(); err != nil {
		log.Fatalf("Failed to start %s: %v", scriptPath, err)
	}
	fmt.Println("MediaPipe helper process started successfully.")
}

func (a *App) processActions(stableGesture string) {
	comboString := a.comboManager.Update(stableGesture)
	fmt.Printf("\nNew stable gesture: %s | Current combo: %s\n", stableGesture, comboString)

	if cmd, ok := a.actionMap[comboString]; ok {
		fmt.Printf("Executing combo action for '%s': %s\n", comboString, cmd)
		executeCommand(comboString, cmd)
		a.comboManager.Reset()
		a.lastActionTime = time.Now()
		a.lastActionGesture = comboString
		return
	}

	if cmd, ok := a.actionMap[stableGesture]; ok {
		if stableGesture != a.lastActionGesture || time.Since(a.lastActionTime) > actionCooldown {
			fmt.Printf("Executing action for '%s': %s\n", stableGesture, cmd)
			executeCommand(stableGesture, cmd)
			a.lastActionTime = time.Now()
			a.lastActionGesture = stableGesture
		}
	}
}

func (a *App) Cleanup() {
	fmt.Println("\nCleaning up resources...")
	if a.pythonCmd != nil && a.pythonCmd.Process != nil {
		fmt.Println("Terminating Python helper process...")
		if err := a.pythonCmd.Process.Kill(); err != nil {
			log.Printf("Failed to kill Python process: %v", err)
		}
		a.pythonCmd.Wait()
	}
	if a.debugMode {
		if a.webcam != nil {
			a.webcam.Close()
		}
	}
	fmt.Println("Cleanup complete.")
}

// --- Gesture Recognizer Logic ---

var allFingers = map[string]bool{"thumb": true, "index": true, "middle": true, "ring": true, "pinky": true}
var landmark = struct {
	WRIST, THUMB_TIP, INDEX_FINGER_MCP, MIDDLE_FINGER_MCP, PINKY_MCP,
	INDEX_FINGER_PIP, INDEX_FINGER_TIP, MIDDLE_FINGER_PIP, MIDDLE_FINGER_TIP,
	RING_FINGER_PIP, RING_FINGER_TIP, PINKY_PIP, PINKY_TIP int
}{0, 4, 5, 9, 17, 6, 8, 10, 12, 14, 16, 18, 20}

const thumbExtensionThreshold = 1.3

func (a *App) recognizeGesture(hand HandData) (string, HandState) {
	if len(hand.Landmarks) < 21 {
		return "", HandState{}
	}
	state := getHandState(hand)
	for name, definition := range a.gestureDefs {
		if checkConditions(state, definition.Conditions) {
			return name, state
		}
	}
	return "", state
}

// ##################################################################
// #                       HERE IS THE FIX                          #
// ##################################################################
func getHandState(hand HandData) HandState {
	lms := hand.Landmarks
	handedness := strings.ToLower(hand.Handedness)

	var isPalmFacing bool
	if handedness == "right" {
		// For a right hand in a mirrored view, palm is facing camera if index MCP has a LARGER x-coord than pinky MCP
		isPalmFacing = lms[landmark.INDEX_FINGER_MCP].X > lms[landmark.PINKY_MCP].X
	} else {
		// For a left hand, palm is facing camera if index MCP has a SMALLER x-coord than pinky MCP
		isPalmFacing = lms[landmark.INDEX_FINGER_MCP].X < lms[landmark.PINKY_MCP].X
	}

	orientation := "back"
	if isPalmFacing {
		orientation = "front"
	}

	fingerStates := FingerStateMap{
		"index":  getFingerState(lms, landmark.INDEX_FINGER_TIP, landmark.INDEX_FINGER_PIP),
		"middle": getFingerState(lms, landmark.MIDDLE_FINGER_TIP, landmark.MIDDLE_FINGER_PIP),
		"ring":   getFingerState(lms, landmark.RING_FINGER_TIP, landmark.RING_FINGER_PIP),
		"pinky":  getFingerState(lms, landmark.PINKY_TIP, landmark.PINKY_PIP),
	}
	palmWidth := dist(lms[landmark.INDEX_FINGER_MCP], lms[landmark.PINKY_MCP])
	thumbDistance := dist(lms[landmark.THUMB_TIP], lms[landmark.PINKY_MCP])
	fingerStates["thumb"] = "curled"
	if thumbDistance > (palmWidth * thumbExtensionThreshold) {
		fingerStates["thumb"] = "extended"
	}
	handVecX := lms[landmark.MIDDLE_FINGER_MCP].X - lms[landmark.WRIST].X
	handVecY := lms[landmark.MIDDLE_FINGER_MCP].Y - lms[landmark.WRIST].Y
	angle := math.Atan2(-handVecY, handVecX) * 180 / math.Pi
	direction := "left"
	if -45 <= angle && angle < 45 {
		direction = "right"
	} else if 45 <= angle && angle < 135 {
		direction = "up"
	} else if -135 <= angle && angle < -45 {
		direction = "down"
	}
	return HandState{
		Handedness: handedness, Orientation: orientation, Direction: direction, Fingers: fingerStates,
	}
}

func checkConditions(state HandState, conds GestureConditions) bool {
	if conds.Handedness != "" && state.Handedness != conds.Handedness {
		return false
	}
	if conds.Orientation != "" && state.Orientation != conds.Orientation {
		return false
	}
	if conds.Direction != "" && state.Direction != conds.Direction {
		return false
	}
	if len(conds.Fingers) > 0 {
		for finger, requiredState := range conds.Fingers {
			if state.Fingers[finger] != requiredState {
				return false
			}
		}
		for finger := range allFingers {
			if _, specified := conds.Fingers[finger]; !specified {
				if state.Fingers[finger] != "curled" {
					return false
				}
			}
		}
	}
	return true
}

func getFingerState(lms []Landmark, tip, pip int) string {
	if dist(lms[tip], lms[landmark.WRIST]) > dist(lms[pip], lms[landmark.WRIST]) {
		return "extended"
	}
	return "curled"
}

// --- Stabilizer, Combo Manager, Executor ---

type GestureStabilizer struct {
	candidateGesture   string
	stableGesture      string
	confirmationFrames int
}

func NewGestureStabilizer() *GestureStabilizer { return &GestureStabilizer{} }
func (s *GestureStabilizer) Update(rawGesture string) string {
	if rawGesture != "" && rawGesture == s.candidateGesture {
		s.confirmationFrames++
	} else {
		s.candidateGesture = rawGesture
		s.confirmationFrames = 1
	}
	if s.confirmationFrames >= confirmationThreshold && s.candidateGesture != s.stableGesture {
		s.stableGesture = s.candidateGesture
	} else if rawGesture == "" {
		s.stableGesture = ""
	}
	return s.stableGesture
}

type ComboManager struct {
	sequence        []string
	lastGestureTime time.Time
}

func NewComboManager() *ComboManager { return &ComboManager{} }
func (c *ComboManager) Update(gestureName string) string {
	now := time.Now()
	if len(c.sequence) > 0 && now.Sub(c.lastGestureTime) > comboTimeout {
		c.sequence = []string{}
	}
	c.sequence = append(c.sequence, gestureName)
	c.lastGestureTime = now
	return strings.Join(c.sequence, "-")
}
func (c *ComboManager) Reset() {
	c.sequence = []string{}
	c.lastGestureTime = time.Time{}
	fmt.Println("Combo sequence reset.")
}
func executeCommand(gesture, command string) {
	cmd := exec.Command("sh", "-c", os.ExpandEnv(command))
	if err := cmd.Start(); err != nil {
		log.Printf("Error starting command '%s': %v", command, err)
	} else {
		go func() {
			cmd.Wait()
			showNotification(gesture, command)
		}()
	}
}
func showNotification(gesture, command string) {
	title := fmt.Sprintf("Gestura: '%s' triggered", gesture)
	parts := strings.Fields(command)
	cmdName := command
	if len(parts) > 0 {
		cmdName = filepath.Base(parts[0])
	}
	message := fmt.Sprintf("Running: %s", cmdName)
	if err := beeep.Notify(title, message, ""); err != nil {
		log.Printf("Failed to show notification: %v", err)
	}
}

// --- Renderer for Debug Mode ---

type HandRenderData struct {
	HandData
	State         HandState
	RawGesture    string
	StableGesture string
}

func DrawDebugInfo(img *gocv.Mat, hands []HandRenderData) {
	frameWidth := img.Cols()
	green := color.RGBA{0, 255, 0, 0}
	red := color.RGBA{255, 0, 0, 0}
	for _, hand := range hands {
		for _, lm := range hand.Landmarks {
			pt := image.Pt(int(lm.X*float64(img.Cols())), int(lm.Y*float64(img.Rows())))
			gocv.Circle(img, pt, 3, green, -1)
		}
		xPos := 50
		if strings.ToLower(hand.Handedness) == "right" {
			xPos = frameWidth - 300
		}
		yPos := 50
		drawText(img, fmt.Sprintf("Raw: %s", Coalesce(hand.RawGesture, "None")), image.Pt(xPos, yPos), color.RGBA{255, 100, 100, 0})
		yPos += 30
		drawText(img, fmt.Sprintf("Stable: %s", Coalesce(hand.StableGesture, "None")), image.Pt(xPos, yPos), color.RGBA{255, 255, 0, 0})
		yPos += 40
		stateInfo := []string{
			fmt.Sprintf("Hand: %s", hand.State.Handedness),
			fmt.Sprintf("Direction: %s", hand.State.Direction),
			fmt.Sprintf("Orientation: %s", hand.State.Orientation),
		}
		for _, info := range stateInfo {
			drawText(img, info, image.Pt(xPos, yPos), color.RGBA{200, 255, 200, 0})
			yPos += 30
		}
		yPos += 10
		for finger, state := range hand.State.Fingers {
			textColor := red
			if state == "extended" {
				textColor = green
			}
			drawText(img, fmt.Sprintf("%s: %s", strings.Title(finger), state), image.Pt(xPos, yPos), textColor)
			yPos += 25
		}
	}
}
func drawText(img *gocv.Mat, text string, pos image.Point, clr color.RGBA) {
	gocv.PutText(img, text, pos, gocv.FontHersheySimplex, 0.6, clr, 2)
}

// --- Utility Functions ---

func loadJSON[T any](path string) (T, error) {
	var data T
	file, err := os.ReadFile(path)
	if err != nil {
		if os.IsNotExist(err) {
			log.Printf("Warning: Config file not found at '%s'. Returning empty map.", path)
			return data, nil
		}
		return data, err
	}
	if err := json.Unmarshal(file, &data); err != nil {
		return data, err
	}
	return data, nil
}
func dist(p1, p2 Landmark) float64 {
	return math.Sqrt(math.Pow(p1.X-p2.X, 2) + math.Pow(p1.Y-p2.Y, 2))
}
func Coalesce(s ...string) string {
	for _, v := range s {
		if v != "" {
			return v
		}
	}
	return ""
}

// --- Main Execution ---

func main() {
	debug := flag.Bool("debug", false, "Enable debug mode to show camera feed with landmarks.")
	flag.Parse()
	app, err := NewApp(*debug)
	if err != nil {
		log.Fatalf("Error initializing application: %v", err)
	}
	app.Run()
}
