func = ['js::jit::MakeMRegExpHoistable ', ' AppKit@0x7be82f ', ' __RtlUserThreadStart ', ' xul.dll@0x1ade7cf ', 'XUL@0x7bd20f', 'libxul.so@0xe477b4 ']

stack_trace = "js::GCMarker::processMarkStackTop | js::GCMarker::drainMarkStack | js::gc::GCRuntime::incrementalCollectSlice | js::gc::GCRuntime::gcCycle | js::gc::GCRuntime::collect | JS::StartIncrementalGC | nsJSContext::GarbageCollectNow | nsTimerImpl::Fire | nsTimerEvent::Run | nsThread::ProcessNextEvent | NS_ProcessPendingEvents | nsBaseAppShell::NativeEventCallback | nsAppShell::ProcessGeckoEvents | CoreFoundation@0xa74b0 | CoreFoundation@0x8861c | CoreFoundation@0x87b15 | CoreFoundation@0x87513 | HIToolbox@0x312ab | HIToolbox@0x310e0 | HIToolbox@0x30f15 | AppKit@0x476cc | AppKit@0x7be82f | CoreFoundation@0x9e3a1 | AppKit@0xc56609 | AppKit@0xc9e7f7 | AppKit@0xc9e387 | AppKit@0xc567a9 | AppKit@0xc5867b | AppKit@0xc57ccc | AppKit@0xc5a9c2 | AppKit@0x47c2ed | AppKit@0x47c304 | AppKit@0xcdcf03 | AppKit@0xc56e2b | AppKit@0xc579af | AppKit@0xcdcee2 | AppKit@0xc5e77b | AppKit@0xc9897a | AppKit@0xc9c88c | AppKit@0xc7f10e"

top_ten_stack_traces = ['js::gcmarker::processmarkstacktop', 'js::gcmarker::drainmarkstack', 'js::gc::gcruntime::incrementalcollectslice', 'js::gc::gcruntime::gccycle', 'js::gc::gcruntime::collect', 'js::startincrementalgc', 'nsjscontext::garbagecollectnow', 'nstimerimpl::fire', 'nstimerevent::run', 'nsthread::processnextevent']