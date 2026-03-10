(function() {
    const syncPlanTypeLogic = () => {
        const container = document.getElementById('modal-content-container');
        if (!container) return;

        const planTypeField = container.querySelector('#id_plan_type');
        
        const getFieldAssets = (id) => {
            const input = container.querySelector(`#${id}`);
            const label = container.querySelector(`label[for="${id}"]`);
            // Since the label and input div are siblings, their parent is the "row"
            const row = label ? label.parentElement : null;
            
            return { input, label, row };
        };

        const commands = getFieldAssets('id_commands');
        const feature = getFieldAssets('id_feature');

        if (!planTypeField || !commands || !feature) return;

        const updateFieldState = (assets, isRequired, isVisible) => {
            // 1. Toggle the entire parent wrapper (hides label + input + select2)
            if (assets.row) {
                if (isVisible) {
                    assets.row.classList.remove('d-none');
                    // Ensure d-flex is restored if it was there originally
                    assets.row.classList.add('d-md-flex'); 
                } else {
                    assets.row.classList.add('d-none');
                    assets.row.classList.remove('d-md-flex');
                }
            }

            // 2. Toggle Required & Asterisk
            if (isRequired) {
                assets.input.setAttribute('required', 'required');
                assets.label?.classList.add('nb-required');
            } else {
                assets.input.removeAttribute('required');
                assets.label?.classList.remove('nb-required');
            }
        };

        const toggleFields = () => {
            const val = planTypeField.value;
            if (val === 'manual') {
                updateFieldState(commands, true, true);
                updateFieldState(feature, false, false);
            } else if (val === 'intended') {
                updateFieldState(feature, true, true);
                updateFieldState(commands, false, false);
            } else {
                updateFieldState(commands, false, false);
                updateFieldState(feature, false, false);
            }
        };

        // standard and Select2 listeners
        planTypeField.addEventListener('change', toggleFields);
        $(planTypeField).on('change', toggleFields);

        toggleFields();
    };

    document.body.addEventListener('htmx:afterSwap', (e) => {
        if (e.detail.target.id === 'modal-content-container') syncPlanTypeLogic();
    });

    syncPlanTypeLogic();
})();
