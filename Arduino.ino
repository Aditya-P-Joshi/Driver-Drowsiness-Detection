const int whiteLED = 6;
const int redLED = 7;

void setup()
{
  pinMode(whiteLED, OUTPUT);
  pinMode(redLED, OUTPUT);

  digitalWrite(whiteLED, HIGH);
  digitalWrite(redLED, LOW);

  Serial.begin(9600);
}

void loop()
{
  if (Serial.available())
  {
    char command = Serial.read();

    // Driver Sleeping
    if (command == 'A')
    {
      digitalWrite(whiteLED, LOW);
      digitalWrite(redLED, HIGH);
    }

    // Driver Awake
    else if (command == 'R')
    {
      digitalWrite(whiteLED, HIGH);
      digitalWrite(redLED, LOW);
    }
  }
}
