 #include <Q2HX711.h>
 #include <RPM.h>

#define RCPin 10   // FrSky receiver throttle channel signal (PWM). Connect signal + ground only; receiver GND must connect to Arduino GND.

// --- Pins ---
const byte HX711_DATA_PIN = 3;
const byte HX711_CLOCK_PIN = 4;
int RCValue;

/* Note for Future Readers! This is the overall thrust test rig code since the end of the 2026 Competition Year.
The code was made with using a HX711 Load Cell, RPM sensor, and Shunt Resistor in mind. It additionally checks for
the throttle level set by the transmitter. Of important note is the calibration number. This should be the main variable
that you may have to change around at the beginning of the semester. Basically, think of the forces that the load cell
experiences to be a linear function. The calibration number acts as the slope of this function. Think f(x)=ax + b. You
can test around to find this number, then check with a testing weight to verify. Note that the load cell outputs force
in kilograms of force, not Newtons. Anyways, hope this helps! */

// --- Sampling / Calibration ---
const int   NUM_READS     = 10;        // samples to average per reading
const int   READ_DELAY_MS = 5;         // delay between samples (ms)
float CALIBRATION   = -213*48.94/50.00; // your calibration factor (counts per unit)

// --- Timing ---
// Time between CSV rows (ms). Exact as long as one loop's readings take less than this
// (check with PRINT_LOOP_TIME). If readings take longer, rows come out as fast as the readings allow.
const unsigned long LOOP_PERIOD_MS = 500;
// true: adds a 4th CSV column = ms spent reading/printing in that loop. Set false once you know your timing.
const bool PRINT_LOOP_TIME = true;

// Final Calibration: 212.5

// --- Globals ---
Q2HX711 hx711(HX711_DATA_PIN, HX711_CLOCK_PIN);
long tare_offset = 0;
long tare_offset2 = 0;

// Average N raw HX711 readings
long readAverageRaw(int n) {
  long sum = 0;
  for (int i = 0; i < n; i++) {
    sum += hx711.read();
    delay(READ_DELAY_MS);
  }
  return sum / n;
}

// Returns the raw throttle pulse width in microseconds (typically ~1000 = zero throttle, ~2000 = full),
// or -1 as a "no signal" marker. No calibration needed - convert to % later in Excel if you want.
// -1 means no pulse was seen on RCPin within 30 ms (signal source off, or signal/ground wire loose).
// The 30 ms timeout covers one full RC frame (~20-22 ms) with margin.
int readThrottle() {
  RCValue = pulseIn(RCPin, HIGH, 30000);
  if (RCValue == 0) {
    return -1;
  }
  return RCValue;
}

void setup() {
  Serial.begin(9600);
  delay(2000);
  RPM.start(EXTERNAL_PULLUP); //no pullup for function generator
  RPM.error(0);


  // Throttle reader setup
  pinMode(RCPin, INPUT);

  // Tare
  Serial.println("Taring...");
  tare_offset = readAverageRaw(NUM_READS);
  Serial.print("Tare offset_1: ");
  Serial.println(tare_offset);
  Serial.println("Complete!");
  delay(2000);

}



void loop() {
  unsigned long loopStart = millis();

  // Read, average, subtract tare
  // Serial.print(CALIBRATION);
  long raw_avg = readAverageRaw(NUM_READS);
  long net     = raw_avg - tare_offset;

  // Convert to thrust units using your calibration factor
  // Serial.print(net);
  float thrust = net / CALIBRATION;
  // NOTE: thrust comes out in whatever unit the calibration weights were in (kg -> kgf, g -> grams-force).
  // It is NOT Newtons unless converted (kgf * 9.81 = N). Record which unit you calibrated with.

  int throttle = readThrottle();

  // Setup as csv output for excel: thrust, throttle pulse (us), rpm[, loop ms]
  Serial.print(thrust);
  Serial.print(", ");
  Serial.print(throttle);
  Serial.print(", ");
  if (PRINT_LOOP_TIME) {
    Serial.print(RPM.get());
    Serial.print(", ");
    Serial.println(millis() - loopStart);
  } else {
    Serial.println(RPM.get());
  }

  // Wait out the rest of the period so rows are exactly LOOP_PERIOD_MS apart (update rate)
  while (millis() - loopStart < LOOP_PERIOD_MS) { }
}
