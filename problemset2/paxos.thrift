
struct PrepareResponse {
  1: bool promised,
  2: string highest_accepted_value,
  3: bool value_is_chosen,
  4: i32 highest_prepared
}
struct PrepareFutureResponse {
  1: bool promised,
  2: list<i32> accepted,
  3: list<string> values,
  4: i32 highest_prepared
}
service Paxos {
  bool Ping()
  // Returns 0 if accepted, or the highest number prepare.
  i32 Propose(1:i32 instance, 2:i32 proposal_number, 3:string value),
  PrepareResponse Prepare(1:i32 instance, 2:i32 proposal_number),
  PrepareFutureResponse PrepareFuture(1:i32 instance, 2:i32 proposal_number),
  void Learn(1:i32 instance, 2:string command),
  oneway void RunCommand(1:i32 cmd_id, 2:i32 node_id, 3:string command),
  void ElectNewLeader(1:i32 new_leader),
  void Kill()
}
