document.addEventListener('DOMContentLoaded', () => {
    const statusDashboard = document.getElementById('status-dashboard');
    const statusMove = document.getElementById('status-move');
    const statusFeed = document.getElementById('status-feed');
    const btnEnable = document.getElementById('btn-enable');
    const btnDisable = document.getElementById('btn-disable');
    const messageBox = document.getElementById('message-box');

    let lastConnectionState = null; // 用於追蹤上一次的整體連線狀態

    // 更新狀態燈的函式
    const updateStatusLight = (element, isConnected) => {
        const currentState = element.classList.contains('green');
        if (currentState !== isConnected) {
            element.classList.remove('gray', 'green', 'red');
            element.classList.add(isConnected ? 'green' : 'red');
        }
    };

    // 顯示訊息的函式
    const showMessage = (message, isError = false) => {
        messageBox.textContent = message;
        messageBox.style.color = isError ? '#c0392b' : '#2c3e50';
    };

    // 檢查與 Dobot 的連線狀態
    const checkConnectionStatus = async (isInitialCheck = false) => {
        if (isInitialCheck) {
            showMessage('正在檢查初始連線狀態...');
        }

        try {
            const response = await fetch('/api/connection/check');
            if (!response.ok) {
                throw new Error(`HTTP 錯誤！ 狀態: ${response.status}`);
            }
            const data = await response.json();
            
            updateStatusLight(statusDashboard, data.dashboard);
            updateStatusLight(statusMove, data.move);
            updateStatusLight(statusFeed, data.feed);

            const allConnected = data.dashboard && data.move && data.feed;

            // 只有當連線狀態改變時才更新訊息
            if (lastConnectionState !== allConnected) {
                if (allConnected) {
                    showMessage('已成功連線至 Dobot。');
                } else {
                    showMessage('Dobot 連線中斷或部分失敗，請檢查硬體與網路設定。', true);
                }
                lastConnectionState = allConnected;
            }

        } catch (error) {
            console.error('檢查連線狀態失敗:', error);
            // 只有當連線狀態改變時才更新訊息
            if (lastConnectionState !== false) {
                showMessage(`無法連接至後端伺服器: ${error.message}`, true);
                lastConnectionState = false;
            }
            updateStatusLight(statusDashboard, false);
            updateStatusLight(statusMove, false);
            updateStatusLight(statusFeed, false);
        }
    };

    // 發送控制指令的通用函式
    const sendControlCommand = async (endpoint, actionName) => {
        showMessage(`正在執行: ${actionName}...`);
        try {
            const response = await fetch(endpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            const data = await response.json();

            if (data.status === 'success') {
                showMessage(`操作成功: ${actionName}\n訊息: ${data.message}`);
            } else {
                showMessage(`操作失敗: ${actionName}\n錯誤: ${data.message}`, true);
            }

        } catch (error) {
            console.error(`${actionName} 失敗:`, error);
            showMessage(`無法發送指令至後端伺服器: ${error.message}`, true);
        }
    };

    // 綁定按鈕事件
    btnEnable.addEventListener('click', () => {
        sendControlCommand('/api/robot/enable', 'Enable Robot');
    });

    btnDisable.addEventListener('click', () => {
        sendControlCommand('/api/robot/disable', 'Disable Robot');
    });

    // 頁面載入時立即執行一次初始檢查
    checkConnectionStatus(true);

    // 設定每 3 秒鐘定期檢查一次連線狀態
    setInterval(() => checkConnectionStatus(false), 3000);
});
