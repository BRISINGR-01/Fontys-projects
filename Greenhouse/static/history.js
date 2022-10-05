const SENSOR_IDS = [
  "q3bPOMgDza",
  "Anw2bNFVHb",
  "rtPGM4n80v",
  "fFPR9fxgIf",
  "seZDwgOPZH",
  "d1ftuVwNyY",
  "sjLDuO4Lx4",
  "mFEYsuCfXe",
  "HyrOWwWXn5",
  "UeAEMUlYOu",
];
const ARDUINO_SENSORS = [];
const WEEKS = [1, 2, 3, 4];
const DAYS = [
  "Monday",
  "Tuesday",
  "Wednesday",
  "Thursday",
  "Friday",
  "Saturday",
  "Sunday",
];

let data, chart, sensor, week, day;

const id = (id) => document.getElementById(id);

function select(type, id) {
  const selected = (document.getElementsByClassName(type + "-selected") ?? [])[0];
  selected?.classList?.remove(type + "-selected");
  document.getElementById(id)?.classList?.add(type + "-selected");
}

function getWeek() {
  let currentDate = new Date();
  let startDate = new Date(currentDate.getFullYear(), 0, 1);
  let days = Math.floor((currentDate - startDate) / (24 * 60 * 60 * 1000));

  return Math.ceil(days / 7);
}

function onTabClick(type, e) {
  select(type, e.target.id);
  let prev_sensor = sensor;

  switch (type) {
    case "sensor":
      sensor = e.target.id.replace("sensor-", "");
      if (ARDUINO_SENSORS.includes(prev_sensor) && !WEEKS.includes(week)) {// if prev sensor was arduino
        select("week", "week-1");
        week = 1;
      }
      break;
    case "week":
      week = Number(e.target.innerText);
      break;
    case "day":
      day = e.target.innerText;
      break;
  }

  localStorage.sensor = sensor;
  localStorage.week = week;
  localStorage.day = day;

  if (data && chart) refreshData();
}

document.addEventListener("DOMContentLoaded", async () => {
  data = await fetch("get_data").then((res) => res.json());
  Object.keys(data).forEach((sensor) => {
    if (!SENSOR_IDS.includes(sensor)) ARDUINO_SENSORS.push(sensor);
  });

  [...ARDUINO_SENSORS, ...SENSOR_IDS].forEach(curr_sensor => {
    const btn = document.createElement("button");
    btn.classList.add("sensor-tab");
    btn.id = "sensor-" + curr_sensor;
    btn.innerText = ARDUINO_SENSORS.includes(curr_sensor) ? curr_sensor : curr_sensor.slice(0,3);
    id("sensor-tabs").appendChild(btn);
  });
  
  Object.keys(data[SENSOR_IDS[0]]).forEach(curr_week => {
    const btn = document.createElement("button");
    btn.classList.add("week-tab");
    btn.id = "week-" + curr_week;
    btn.innerText = curr_week;
    id("week-tabs").appendChild(btn);
  })


  sensor = [...SENSOR_IDS, ...ARDUINO_SENSORS].includes(localStorage.sensor)
    ? localStorage.sensor
    : SENSOR_IDS[0];
  week = +localStorage.week in data[sensor] ? +localStorage.week : WEEKS[0],
  day = DAYS.includes(localStorage.day) ? localStorage.day : "Monday";

  select("sensor", "sensor-" + sensor);
  select("week", "week-" + week);
  select("day", "day-" + (DAYS.indexOf(day) + 1));

  if (ARDUINO_SENSORS.includes(sensor)) {
    let unAvailableDays = Object.entries(data[sensor][week])
      .filter(([day, val]) => val.length == 0)
      .map(([day, val]) => day);

    let availableDays = DAYS.filter((d) => !unAvailableDays.includes(d));
    if (availableDays.length == 0) {
      day = DAYS[0];
      select("day", "day-1");
    } else {
      day = availableDays[0];
      select("day", "day-" + (DAYS.indexOf(day) + 1));
    }
  }

  ["sensor", "week", "day"].forEach((type) =>
    [...document.getElementsByClassName(type + "-tab")].forEach(
      (tab) => (tab.onclick = (e) => onTabClick(type, e))
    )
  );

  Chart.defaults.global.defaultFontColor = "#ffc800";

  if (data[sensor][week][day].length == 0) {
    day = (Object.entries(data[sensor][week]).find(
      ([day, val]) => val.length > 0
    ) ?? DAYS)[0];
    select("day", "day-" + (DAYS.indexOf(day) + 1));
  }

  const temperatureValues = data[sensor][week][day].map((val) => val[4]);
  const humidityValues = data[sensor][week][day].map((val) => val[5]);
  const brightnessValues = data[sensor][week][day].map((val) => val[6]);
  const hours = data[sensor][week][day].map((val) => val[3]);

  chart = new Chart("graph", {
    type: "line",
    data: {
      labels: hours,
      datasets: [
        {
          label: "temperature",
          borderColor: "red",
          data: temperatureValues,
        },
        {
          label: "humidity",
          borderColor: "blue",
          data: humidityValues,
        },
        {
          label: "brightness (x 0.1)",
          borderColor: "yellow",
          data: brightnessValues.map((l) => l / 10), // for display purposes (makes the graph inaccurate for values)
        },
      ],
    },
  });

  refreshData()
});


function refreshData() {
  const historyTable = id("history");
  historyTable.querySelectorAll("*").forEach((child) => child.remove());
  const statisticsTable = id("statistics");

  if (
    data[sensor][week][day].length == 0
  ) {
    statisticsTable
      .querySelectorAll(".statistics-cell")
      .forEach((child) => (child.innerText = ""));

    chart.data.labels = [];
    chart.data.datasets.forEach((dataset, i) => {
      dataset.data = [];
    });
    if (chart) {
      chart.update();
    }

    return;
  }

  dayData = data[sensor][week][day];

  dayData.forEach((val) => {
    const row = document.createElement("tr");

    val.slice(3).forEach((d) => {
      const cell = document.createElement("td");
      cell.innerText = d;
      row.appendChild(cell);
    });

    historyTable.appendChild(row);
  });

  const temperatureValues = data[sensor][week][day].map((val) => val[4]);
  const humidityValues = data[sensor][week][day].map((val) => val[5]);
  let brightnessValues = data[sensor][week][day].map((val) => val[6]);
  const hours = data[sensor][week][day].map((val) => val[3]);

  id("average-temperature-day").innerText = Math.round(
    temperatureValues.map(Number).reduce((a, n) => a + n) / hours.length
  );
  id("average-humidity-day").innerText = Math.round(
    humidityValues.map(Number).reduce((a, n) => a + n) / hours.length
  );
  id("average-brightness-day").innerText = Math.round(
    brightnessValues.map(Number).reduce((a, n) => a + n) / hours.length
  );

  id("max-temperature-day").innerText = temperatureValues
    .map(Number)
    .reduce((a, n) => Math.max(a, n));
  id("max-humidity-day").innerText = humidityValues
    .map(Number)
    .reduce((a, n) => Math.max(a, n));
  id("max-brightness-day").innerText = brightnessValues
    .map(Number)
    .reduce((a, n) => Math.max(a, n));

  id("min-temperature-day").innerText = temperatureValues
    .map(Number)
    .reduce((a, n) => Math.min(a, n));
  id("min-humidity-day").innerText = humidityValues
    .map(Number)
    .reduce((a, n) => Math.min(a, n));
  id("min-brightness-day").innerText = brightnessValues
    .map(Number)
    .reduce((a, n) => Math.min(a, n));

  let week_temp_val = [];
  let week_hum_val = [];
  let week_lux_val = [];

  for (curr_day in data[sensor][week]) {
    if (!data[sensor][week][curr_day]) continue;

    week_temp_val = week_temp_val.concat(
      ...data[sensor][week][curr_day].map((val) => val[4])
    );
    week_hum_val = week_hum_val.concat(
      ...data[sensor][week][curr_day].map((val) => val[5])
    );
    week_lux_val = week_lux_val.concat(
      ...data[sensor][week][curr_day].map((val) => val[6])
    );
  }

  id("average-temperature-week").innerText = Math.round(
    week_temp_val.map(Number).reduce((a, n) => a + n) / week_temp_val.length
  );
  id("average-humidity-week").innerText = Math.round(
    week_hum_val.map(Number).reduce((a, n) => a + n) / week_hum_val.length
  );
  id("average-brightness-week").innerText = Math.round(
    week_lux_val.map(Number).reduce((a, n) => a + n) / week_lux_val.length
  );

  id("max-temperature-week").innerText = week_temp_val
    .map(Number)
    .reduce((a, n) => Math.max(a, n));
  id("max-humidity-week").innerText = week_hum_val
    .map(Number)
    .reduce((a, n) => Math.max(a, n));
  id("max-brightness-week").innerText = week_lux_val
    .map(Number)
    .reduce((a, n) => Math.max(a, n));

  id("min-temperature-week").innerText = week_temp_val
    .map(Number)
    .reduce((a, n) => Math.min(a, n));
  id("min-humidity-week").innerText = week_hum_val
    .map(Number)
    .reduce((a, n) => Math.min(a, n));
  id("min-brightness-week").innerText = week_lux_val
    .map(Number)
    .reduce((a, n) => Math.min(a, n));

  let sensor_temp_val = [];
  let sensor_hum_val = [];
  let sensor_lux_val = [];

  for (curr_week in data[sensor]) {
    for (curr_day in data[sensor][week]) {
      if (!data[sensor][curr_week][curr_day]) continue;

      sensor_temp_val = sensor_temp_val.concat(
        ...data[sensor][curr_week][curr_day].map((val) => val[4])
      );
      sensor_hum_val = sensor_hum_val.concat(
        ...data[sensor][curr_week][curr_day].map((val) => val[5])
      );
      sensor_lux_val = sensor_lux_val.concat(
        ...data[sensor][curr_week][curr_day].map((val) => val[6])
      );
    }
  }

  id("average-temperature-sensor").innerText = Math.round(
    sensor_temp_val.map(Number).reduce((a, n) => a + n) / sensor_temp_val.length
  );
  id("average-humidity-sensor").innerText = Math.round(
    sensor_hum_val.map(Number).reduce((a, n) => a + n) / sensor_hum_val.length
  );
  id("average-brightness-sensor").innerText = Math.round(
    sensor_lux_val.map(Number).reduce((a, n) => a + n) / sensor_lux_val.length
  );

  id("max-temperature-sensor").innerText = sensor_temp_val
    .map(Number)
    .reduce((a, n) => Math.max(a, n));
  id("max-humidity-sensor").innerText = sensor_hum_val
    .map(Number)
    .reduce((a, n) => Math.max(a, n));
  id("max-brightness-sensor").innerText = sensor_lux_val
    .map(Number)
    .reduce((a, n) => Math.max(a, n));

  id("min-temperature-sensor").innerText = sensor_temp_val
    .map(Number)
    .reduce((a, n) => Math.min(a, n));
  id("min-humidity-sensor").innerText = sensor_hum_val
    .map(Number)
    .reduce((a, n) => Math.min(a, n));
  id("min-brightness-sensor").innerText = sensor_lux_val
    .map(Number)
    .reduce((a, n) => Math.min(a, n));

  if (chart) {
    brightnessValues = brightnessValues.map((lux) => lux / 10);

    if (hours.length > chart.data.labels.length) {
      // prevent ugly transition
      // chart.data.labels = hours
      chart.data.datasets.forEach((dataset, i) => {
        dataset.data = temperatureValues.map((el) => 110);
      });
      chart.update();
    }
    chart.data.labels = hours;
    chart.data.datasets.forEach((dataset, i) => {
      dataset.data = [temperatureValues, humidityValues, brightnessValues][i];
    });
    chart.update();
  }
}
