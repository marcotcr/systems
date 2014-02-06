
struct PrepareResponse {
  1: bool promised,
  2: string highest_accepted_value,
  3: bool value_is_chosen,
  4: i32 highest_prepared
}
service Paxos {
  bool Ping()
  // Returns 0 if accepted, or the highest number prepare.
  i32 Propose(1:i32 instance, 2:i32 proposal_number, 3:string value),
  PrepareResponse Prepare(1:i32 instance, 2:i32 proposal_number),
  PrepareResponse PrepareFuture(1:i32 proposal_number),
  oneway void RunCommand(1:i32 cmd_id, 2:string command) 
}
