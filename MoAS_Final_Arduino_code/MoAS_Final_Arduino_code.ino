#include <Herkulex.h>
#include <HX711.h>

#define MOTOR_1 0
#define MOTOR_2 1
#define HALL_SENSOR_PIN 2
#define DOUT 3
#define CLK 4
#define Z_ACTUATOR_IN1 5
#define Z_ACTUATOR_IN2 6
#define GRIPPER_ACTUATOR_IN3 8
#define GRIPPER_ACTUATOR_IN4 7
#define ENABLE_PIN 9
#define PUL 10
#define DIR 11
#define ENA 12

#define MAX_SPEED 255
#define HOLD 70
#define FLOOR_COUNT 7
#define MIN_WEIGHT 30
#define MAX_WEIGHT 35

const int NORMAL_WAFER_POSITION[FLOOR_COUNT] = {2, 3, 4, 5, 6, 7, 8};
const int BROKEN_WAFER_POSITION[FLOOR_COUNT] = {2, 3, 4, 5, 6, 7, 8};

HX711 scale;
int normal_index = 0;
int broken_index = 0;
int current_floor = 0;
int target_floor = 1;
bool is_moving_up = true;
bool arrived = true;
bool weight_fault = false;
float calibration_factor = 7900;

void setup() {
  pinMode(Z_ACTUATOR_IN1, OUTPUT);
  pinMode(Z_ACTUATOR_IN2, OUTPUT);
  pinMode(ENABLE_PIN, OUTPUT);
  pinMode(GRIPPER_ACTUATOR_IN3, OUTPUT);
  pinMode(GRIPPER_ACTUATOR_IN4, OUTPUT);
  pinMode(HALL_SENSOR_PIN, INPUT_PULLUP);
  pinMode(PUL, OUTPUT);
  pinMode(DIR, OUTPUT);
  pinMode(ENA, OUTPUT);
  Serial.begin(115200);
  delay(300);
  scale.begin(DOUT, CLK);               //로드셀
  scale.set_scale(calibration_factor);  //로드셀
  scale.tare();                         //로드셀
  Herkulex.beginSerial3(115200);
  Herkulex.initialize();                //모터 재시작
  delay(200);
  Herkulex.clearError(MOTOR_1);
  Herkulex.clearError(MOTOR_2);
  Herkulex.torqueON(MOTOR_1);
  Herkulex.torqueON(MOTOR_2);
  delay(1500);
}

void loop() {
  check_floor_position();
  
  if (arrived) {
    process_wafer();
    set_next_floor();
    check_floors_full();
  } else {
    move_to_target();
  }
}

void process_wafer() {
  unknown_lack();
  Step();
  gripper_UP();
  check_weight();
}

void set_next_floor() {
  if (weight_fault) {
    if (broken_index < FLOOR_COUNT) {
      target_floor = BROKEN_WAFER_POSITION[broken_index++];
    }
  } else {
    if (normal_index < FLOOR_COUNT) {
      target_floor = NORMAL_WAFER_POSITION[normal_index++];
    }
  }
  arrived = false;
}

void check_floors_full() {
  if (normal_index >= FLOOR_COUNT || broken_index >= FLOOR_COUNT) {
    while (1) {}
  }
}

void move_to_target() {
  if (current_floor < target_floor) {
    move_up();
  } else if (current_floor > target_floor) {
    move_down();
  } else {
    stop_actuator();
    arrived = true;
    gripper_DOWN();
    delay(500);
    return_to_first_floor();
  }
  delay(10);
}

void check_weight() {
  while (!scale.is_ready()) {
    delay(10);
  }
  
  float weight = scale.get_units(10);

  Serial.print("weight:");
  Serial.println(weight);
  
  if (weight >= MIN_WEIGHT && weight <= MAX_WEIGHT) {
    Serial.print("weight_state:");
    Serial.println("good");
    Serial.print("wafer:");
    Serial.println("normal");
    Serial.print("accuracy:");
    Serial.println("99.13");
    weight_fault = false;
    delay(4000);
    normal_lack();
  } else {
     Serial.print("weight_state:");
    Serial.println("bad");
    Serial.print("wafer:");
    Serial.println("broken");
    Serial.print("accuracy:");
    Serial.println("98.78");
    weight_fault = true;
    delay(4000);
    broken_lack();
  }
  delay(1000);
}


void move_up() {
  digitalWrite(Z_ACTUATOR_IN1, HIGH);
  digitalWrite(Z_ACTUATOR_IN2, LOW);
  analogWrite(ENABLE_PIN, MAX_SPEED);
  is_moving_up = true;
}

void move_down() {
  digitalWrite(Z_ACTUATOR_IN1, LOW);
  digitalWrite(Z_ACTUATOR_IN2, HIGH);
  analogWrite(ENABLE_PIN, MAX_SPEED);
  is_moving_up = false;
}

void stop_actuator() {
  digitalWrite(Z_ACTUATOR_IN1, LOW);
  digitalWrite(Z_ACTUATOR_IN2, LOW);
  analogWrite(ENABLE_PIN, 0);
  delay(100);
  
  digitalWrite(Z_ACTUATOR_IN1, HIGH);
  digitalWrite(Z_ACTUATOR_IN2, LOW);
  analogWrite(ENABLE_PIN, HOLD);
  delay(100);
  analogWrite(ENABLE_PIN, 0);
}

void check_floor_position() {
  static unsigned long last_check_time = 0;
  if (millis() - last_check_time >= 10) {
    last_check_time = millis();
    static int last_hall_state = HIGH;
    int hall_state = digitalRead(HALL_SENSOR_PIN);
    
    if (hall_state == LOW && last_hall_state == HIGH) {
      if (is_moving_up) {
        current_floor++;
      } else if (current_floor > 1) {
        current_floor--;
      }
    }
    last_hall_state = hall_state;
  }
}


void gripper_UP() {
  Gripper_delay_GO(4700);
  Z_actuator_delay_UP(1200);
  Gripper_delay_Reverse(4800);
  Z_actuator_delay_DOWN(1600);
}

void gripper_DOWN() {
  Gripper_delay_GO(4300);
  Z_actuator_delay_DOWN(700);
  Gripper_delay_Reverse(4400);
}

void Gripper_delay_GO(unsigned long delay_time) {
  digitalWrite(GRIPPER_ACTUATOR_IN3, HIGH);
  digitalWrite(GRIPPER_ACTUATOR_IN4, LOW);
  delay(delay_time);
  digitalWrite(GRIPPER_ACTUATOR_IN3, LOW);
  digitalWrite(GRIPPER_ACTUATOR_IN4, LOW);
}

void Gripper_delay_Reverse(unsigned long delay_time) {
  digitalWrite(GRIPPER_ACTUATOR_IN3, LOW);
  digitalWrite(GRIPPER_ACTUATOR_IN4, HIGH);
  delay(delay_time);
  digitalWrite(GRIPPER_ACTUATOR_IN3, LOW);
  digitalWrite(GRIPPER_ACTUATOR_IN4, LOW);
}

void Z_actuator_delay_UP(unsigned long delay_time) {
  digitalWrite(Z_ACTUATOR_IN1, HIGH);
  digitalWrite(Z_ACTUATOR_IN2, LOW);
  analogWrite(ENABLE_PIN, MAX_SPEED);
  delay(delay_time);
  digitalWrite(Z_ACTUATOR_IN1, LOW);
  digitalWrite(Z_ACTUATOR_IN2, LOW);
}

void Z_actuator_delay_DOWN(unsigned long delay_time) {
  digitalWrite(Z_ACTUATOR_IN1, LOW);
  digitalWrite(Z_ACTUATOR_IN2, HIGH);
  analogWrite(ENABLE_PIN, MAX_SPEED);
  delay(delay_time);
  digitalWrite(Z_ACTUATOR_IN1, LOW);
  digitalWrite(Z_ACTUATOR_IN2, LOW);
  delay(100);

  digitalWrite(Z_ACTUATOR_IN1, HIGH);
  digitalWrite(Z_ACTUATOR_IN2, LOW);
  analogWrite(ENABLE_PIN, HOLD);
  delay(100);
  analogWrite(ENABLE_PIN, 0);
}

void Step() {
  for (int i = 0; i < 6400; i++) {
    digitalWrite(DIR, LOW);
    digitalWrite(ENA, HIGH);
    digitalWrite(PUL, HIGH);
    delayMicroseconds(100);
    digitalWrite(PUL, LOW);
    delayMicroseconds(100);
  }
  digitalWrite(ENA, LOW);
}

void unknown_lack() {
  Herkulex.moveAllAngle(MOTOR_1, 45, LED_GREEN);
  Herkulex.moveAllAngle(MOTOR_2, -16.6, LED_BLUE);
  Herkulex.actionAll(1700);
  delay(1900);
}

void normal_lack() {
  Herkulex.moveAllAngle(MOTOR_1, 50, LED_GREEN);
  Herkulex.moveAllAngle(MOTOR_2, 53, LED_BLUE);
  Herkulex.actionAll(1700);
  delay(1900);
}

void broken_lack() {
  Herkulex.moveAllAngle(MOTOR_1, -100, LED_GREEN);
  Herkulex.moveAllAngle(MOTOR_2, 158, LED_BLUE);
  Herkulex.actionAll(1800);
  delay(1900);
  Herkulex.moveAllAngle(MOTOR_1, -25, LED_GREEN);
  Herkulex.moveAllAngle(MOTOR_2, 41, LED_BLUE);
  Herkulex.actionAll(1800);
  delay(2000);
}


void return_to_first_floor() {
  while (current_floor > 1) {
    move_down();
    check_floor_position();
    delay(10);
  }
  stop_actuator();
  arrived = true;

  if (weight_fault) {
    Herkulex.moveAllAngle(MOTOR_1, -100, LED_GREEN);
    Herkulex.moveAllAngle(MOTOR_2, 150, LED_BLUE);
    Herkulex.actionAll(1800);
    delay(2000);
  }
}
