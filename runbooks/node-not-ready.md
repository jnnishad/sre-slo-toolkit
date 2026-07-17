# Runbook: Node NotReady

**Triggered by:** a Kubernetes node transitions to `NotReady` for more
than a few minutes (kubelet stops reporting node status heartbeats).

## 1. Confirm scope

```bash
kubectl get nodes -o wide
kubectl describe node <node-name>
```

Check `Conditions` at the bottom of the describe output — the reason
matters:

- `KubeletNotReady` with a network-plugin error -> CNI issue
- `MemoryPressure` / `DiskPressure` -> resource exhaustion on the node
- No recent heartbeat at all, node otherwise looks configured fine -> likely kubelet crash or node-level network partition

## 2. Is this one node or many?

If multiple nodes went `NotReady` at the same time, suspect a shared
dependency: control-plane connectivity, a cluster-wide CNI/DNS issue,
or (in a hybrid/on-prem setup like OpenStack + AWS) a networking change
on the shared substrate rather than anything Kubernetes-specific.

If it's a single node, treat it as a node-local hardware/OS issue.

## 3. Check what's still running on it

```bash
kubectl get pods --all-namespaces --field-selector spec.nodeName=<node-name>
```

Pods on a `NotReady` node are not automatically evicted until the
`node.kubernetes.io/unreachable` taint's toleration window expires
(default 5 minutes) — if this is urgent, don't wait for the default:

```bash
kubectl drain <node-name> --ignore-daemonsets --delete-emptydir-data --force
```

This is the same PDB-aware, DaemonSet-excluding decision logic covered
in [`python-devops-toolkit`'s `k8s_drain.py`](https://github.com/jnnishad/python-devops-toolkit) —
`kubectl drain` handles the same cases, but that module exists for
scripted/CI-triggered drains where you need it as a library, not a CLI
someone runs by hand mid-incident.

## 4. Diagnose and recover the node

- SSH/console access: `journalctl -u kubelet -n 200 --no-pager`
- On-prem (OpenStack): check hypervisor-level health for the VM before
  assuming it's an OS-level problem
- If unrecoverable in a reasonable time, cordon it permanently and
  replace: `kubectl delete node <node-name>` once workloads are safely
  rescheduled elsewhere

## 5. After recovery

- Uncordon if you cordoned but didn't delete: `kubectl uncordon <node-name>`
- Verify workloads rescheduled correctly and are healthy
- If this was caused by a systemic issue (not a one-off hardware
  fault), open a postmortem
