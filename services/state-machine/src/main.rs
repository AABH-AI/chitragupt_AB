mod ac;
mod error;
mod gates;
mod state;

use tracing::info;
use uuid::Uuid;

use gates::manager::GateManager;
use state::phase::SessionPhase;
use state::session::SessionState;
use state::transition::TransitionEngine;

#[tokio::main]
async fn main() -> anyhow::Result<()> {
    tracing_subscriber::fmt()
        .with_env_filter(
            tracing_subscriber::EnvFilter::try_from_default_env()
                .unwrap_or_else(|_| tracing_subscriber::EnvFilter::new("info")),
        )
        .init();

    info!("Chitragupt state machine kernel starting");

    // Smoke-test: create a fresh session and exercise the core types.
    let workspace_id = Uuid::new_v4();
    let project_id = Uuid::new_v4();
    let state = SessionState::new(workspace_id, project_id);
    let gate_manager = GateManager::new();

    info!(
        session_id = %state.session_id,
        phase = %state.current_phase,
        "new session created"
    );

    // Show valid transitions from the initial phase.
    let transitions = state.current_phase.valid_transitions();
    info!(
        "valid transitions from {:?}: {:?}",
        state.current_phase, transitions
    );

    // Evaluate AC for the current phase (all will be unmet on a fresh session).
    let ac_result = state.current_phase.evaluate_ac(&state);
    info!(
        met = ac_result.met_count(),
        unmet = ac_result.unmet_count(),
        transition_ready = ac_result.transition_ready,
        "AC evaluation for {:?}",
        state.current_phase
    );

    if !ac_result.gaps.is_empty() {
        info!("first gap → {}", ac_result.gaps[0].suggested_question);
    }

    // Show open gates (all hard gates open on fresh session).
    let open_gates = gate_manager.open_gates(&state);
    info!("{} gate(s) currently open", open_gates.len());
    for gate in &open_gates {
        info!("  [{:?}] {} — open: {}", gate.gate_type, gate.id, gate.is_open);
    }

    // Attempt transition (will fail — AC not met, hard gates open).
    match TransitionEngine::attempt(&state, SessionPhase::StakeholderDiscovery, &gate_manager) {
        Ok(()) => info!("transition approved (unexpected on fresh session)"),
        Err(e) => info!("transition blocked as expected: {}", e),
    }

    info!("state machine kernel smoke test complete");

    // TODO: Sprint 1 EPIC-1 — wire gRPC server here
    // let addr = "[::1]:50051".parse()?;
    // Server::builder()
    //     .add_service(StateEngineServer::new(StateEngineService::new()))
    //     .serve(addr)
    //     .await?;

    Ok(())
}
