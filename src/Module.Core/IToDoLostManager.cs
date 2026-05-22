namespace Lab.Interfaces;

public interface IToDoListManager
{
    void AddTask(string description);
    void RemoveTask(int id);
    void MarkTaskAsCompleted(int id);
    string[] GetTasks();
}
