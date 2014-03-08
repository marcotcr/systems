service LoadBalancer {
  string GetNode(),
  void SetNodes(1:map<string, string> state)
}
service Worker {
  double Predict(1:i32 id, 2:string x),
  void Learn(1:string x, 2:double y),
  /* Learn from a previously predicted example that has been kept in memory */
  void LearnFromID(1:i32 id, 2:double y),
  double AvgPredictionTime(),
  oneway void Test()
}
